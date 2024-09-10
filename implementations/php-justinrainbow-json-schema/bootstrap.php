<?php

declare(strict_types=1);

use JsonRainbow\TestHarness;

ini_set('display_errors', 'stderr');
require_once 'vendor/autoload.php';

$in = fopen('php://stdin', 'rb');
$out = fopen('php://stdout', 'wb');
$debug = fopen('php://stderr', 'wb');
$testHarness = new TestHarness($in, $out, $debug);
$testHarness();
