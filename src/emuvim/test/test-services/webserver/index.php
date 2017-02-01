<?php
$contents = file_get_contents("/tmp/son_emu_data");
$results = json_decode($contents, true);
$intfs = $results["son_emu_data"]["interfaces"];
$servername = current($intfs)[0];
$username = "admin";
$password = "123";

echo "<br>";
echo gethostname();
echo "<br>";
// Create connection
$conn = new mysqli($servername, $username, $password, "testapp");
// Check connection
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}
$sql = "SELECT firstname FROM cooltable";
$res = $conn->query($sql);

while($row = mysqli_fetch_assoc($res)){
        echo $row["firstname"];
        echo "<br>";
}
$res->free();
$newname = gethostname() . " is cool!";
$sql = "INSERT INTO cooltable (firstname) VALUES ('$newname')";
$conn->query($sql);

$conn->close();
?>