<?php

$ip = getenv ( "SON_EMU_OUT_PARTNER" );
$ips = preg_split('/:/',$ip, PREG_SPLIT_NO_EMPTY);
$servername = $ips[0];
$username = "admin";
$password = "123";

// Create connection
$conn = new mysqli($servername, $username, $password);
// Check connection
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

// Create database
$sql = "CREATE DATABASE testapp";
if ($conn->query($sql) === TRUE) {
    echo "Database created successfully";
} else {
    die "Error creating database: " . $conn->error;
}

$sql = "CREATE TABLE cooltable (
id INT(6) UNSIGNED AUTO_INCREMENT PRIMARY KEY,
firstname VARCHAR(30) NOT NULL
)";

if ($conn->query($sql) === FALSE) {
    die "Error creating table: " . $conn->error;
}

$sql = "INSERT INTO cooltable (firstname)
VALUES ('PG-SANDMAN')";

if ($conn->query($sql) === FALSE) {
    die "Error adding pg-sandman: " . $conn->error;
}


$conn->close();
?> 
