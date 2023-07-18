<?php

$stdout = fopen('php://stdout', 'w');
fwrite($stdout, "Hello, Docker!\n");
fwrite($stdout, "This is printed to the terminal.\n");
fclose($stdout);

echo "Hello, Docker!";
