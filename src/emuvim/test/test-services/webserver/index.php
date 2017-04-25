<html>
<body>
<?php
$contents = file_get_contents("/tmp/son_emu_data");
$results = json_decode($contents, true);
$intfs = $results["son_emu_data"]["interfaces"];
$servername = current($intfs)[0];
$username = "admin";
$password = "123";

echo "<br><b>";
echo gethostname();
echo "</b><br>";
// Create connection
$conn = new mysqli($servername, $username, $password, "testapp");
// Check connection
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}
$sql = "SELECT firstname,counter FROM cooltable";
$res = $conn->query($sql);

while($row = mysqli_fetch_assoc($res)){
        echo $row["firstname"];
        echo "&nbsp;";
        echo $row["counter"];
        echo "<br>";
}
if (!is_bool($res)) {
    $res->free();
}
$newname = gethostname() . " is cool!";
$sql = "INSERT INTO cooltable (firstname,counter) VALUES ('$newname',0) ON DUPLICATE KEY UPDATE counter = counter + 1";
$conn->query($sql);

$conn->close();
?>
</body>
</html>
