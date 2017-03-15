<?php
$contents = file_get_contents("/tmp/son_emu_data.json");
$results = json_decode($contents, true);
$intfs = $results["son_emu_data"]["interfaces"];
echo "";

$servername = current($intfs)[0];
$username = "admin";
$password = "123";

// Create connection
$conn = new mysqli($servername, $username, $password);
// Check connection
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}
// Create database
$sql = "CREATE DATABASE testapp;";
if ($conn->query($sql) === TRUE) {
    echo "Database created successfully";
}

$conn->select_db("testapp");
$sql = "CREATE TABLE cooltable (firstname VARCHAR(30) NOT NULL KEY, counter INT);";

$conn->query($sql);

$sql = "INSERT INTO cooltable (firstname, counter) VALUES ('PG-SANDMAN', 1)";

$conn->query($sql);


$conn->close();
?>
