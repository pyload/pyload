<?php

$x = login();
$x = substr($x, 1, strlen($x) - 2);
$y = api_request('statusServer', $x);
$z = api_request('statusDownloads', $x);

echo "X = ";
var_dump($x);
echo "\nY:";
var_dump($y);
echo "\nZ:";
var_dump($z);

die();

function api_request($method, $key = '', $params = array()) {
    $url = 'http://localhost/api/' . $method;
    $port = 8000;
    $fields_string = '';
    $fields_string = strlen($key) ? 'session=' . $key : '';
    if (count($params)) {
        //url-ify the data for the POST
        foreach($params as $key=>$value) {
            $fields_string .= $key.'='.$value.'&';
        }
        rtrim($fields_string, '&');
        $fields_string = substr($fields_string, 0, strlen($fields_string) - 1);
    }
    
    //open connection
    $ch = curl_init();
    //set the url, number of POST vars, POST data
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_PORT, $port);
    curl_setopt($ch, CURLOPT_POST, count($params));
    curl_setopt($ch, CURLOPT_POSTFIELDS, $fields_string);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

    //execute post
    $result = curl_exec($ch);

    //close connection
    curl_close($ch);
    
    return $result;
}

function login() {
    $method = 'login';
    $fields = array(
        'username' => urlencode('api'),
        'password' => urlencode('apiapi'),
    );
    return api_request($method, '', $fields);
}