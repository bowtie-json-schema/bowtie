<?php

declare(strict_types=1);

namespace JsonRainbow;

use Composer\InstalledVersions;
use JsonSchema\Constraints\Constraint;
use JsonSchema\Constraints\Factory;
use JsonSchema\SchemaStorage;
use JsonSchema\Validator;
use RuntimeException;
use stdClass;
use Throwable;

class TestHarness
{
    private mixed $in;
    private mixed $out;
    private mixed $debug;

    private ?string $currentDialect = null;

    public function __construct($in, $out, $debug)
    {
        get_resource_type($in) !== 'stream' && throw new RuntimeException('Param #1 $in must be a stream');
        get_resource_type($out) !== 'stream' && throw new RuntimeException('Param #2 $out must be a stream');
        get_resource_type($debug) !== 'stream' && throw new RuntimeException('Param #3 $debug must be a stream');

        $this->in = $in;
        $this->out = $out;
        $this->debug = $debug;
    }

    public function __invoke(): void
    {
        $this->debug('Test harness is being invoked');

        while (true) {
            $next = trim(fgets($this->in));
            if ($next === false || $next === '') {
                throw new RuntimeException('Unable to read from input');
            }
            $request = json_decode($next, false, 512, JSON_THROW_ON_ERROR);

            $response = match ($request->cmd) {
                'start' => $this->start($request),
                'stop' => $this->stop(),
                'dialect' => $this->dialect($request),
                'run' => $this->run($request),
                default => [
                    'seq' => $request->seq,
                    'results' => [[
                        'errored' => true,
                        'context' => [
                            'message' => sprintf('Received unsupported command: %s', $request->cmd),
                        ],
                    ]],
                ],
            };

            fwrite($this->out, json_encode($response, JSON_THROW_ON_ERROR) . PHP_EOL);
        }
    }

    private function start(stdClass $request): array
    {
        if ($request->version !== 1) {
            throw new RuntimeException('Unsupported IHOP version');
        }

        $this->debug(
            'Starting with justinrainbow/json-schema version %s',
            InstalledVersions::getVersion('justinrainbow/json-schema')
        );

        return [
            'version' => 1,
            'implementation' => [
                'name' => 'justinrainbow-json-schema',
                'version' => InstalledVersions::getVersion('justinrainbow/json-schema'),
                'homepage' => 'https://github.com/jsonrainbow/json-schema',
                'documentation' => 'https://github.com/jsonrainbow/json-schema/wiki',
                'source' => 'https://github.com/jsonrainbow/json-schema',
                'issues' => 'https://github.com/jsonrainbow/json-schema/issues',
                'dialects' => [
                    'https://json-schema.org/draft/2019-09/schema',
                    'http://json-schema.org/draft-07/schema#',
                    'http://json-schema.org/draft-06/schema#',
                    'http://json-schema.org/draft-04/schema#',
                    'http://json-schema.org/draft-03/schema#',
                ],
                'language' => 'php',
                'language_version' => PHP_VERSION,
                'os' => rtrim(shell_exec('lsb_release -is')),
                'os_version' => rtrim(shell_exec('lsb_release -rs')),
            ],
        ];
    }

    private function stop(): never
    {
        $this->debug('Stopping test harness');
        exit(0);
    }

    private function dialect(stdClass $request): array
    {
        $this->currentDialect = $request->dialect;
        return ['ok' => true];
    }

    private function run(stdClass $request): array
    {
        $this->debug('Running test case with seq: %d', $request->seq);

        $results = [];

        $schemaStorage = new SchemaStorage();
        $factory = new Factory($schemaStorage);
        $validator = new Validator($factory);
        $factory->setDefaultDialect($this->currentDialect ?? $factory->getDefaultDialect());
        $schemaStorage->addSchema('internal://mySchema', $request->case->schema);

        if (isset($request->case->registry)) {
            foreach ($request->case->registry as $id => $schema) {
                $schemaStorage->addSchema($id, $schema);
            }
        }

        foreach ($request->case->tests as $index => $test) {
            try {
                $validator->validate(
                    $test->instance,
                    $request->case->schema,
                    $this->checkMode(),
                );
                $results[] =  ['valid' => $validator->isValid()];
            } catch (Throwable $e) {
                $this->debug('Test case with seq: %d, test index: %d has thrown an exception: %s', $request->seq, $index, $e->getMessage());
                $results[] = [
                    'errored' => true,
                    'context' => [
                        'message' => $e->getMessage(),
                        'traceback' => $e->getTraceAsString(),
                    ],
                ];
            }
        }
        return ['seq' => $request->seq, 'results' => $results];
    }

    private function debug(string $format, ...$values): void
    {
        fwrite($this->debug, sprintf($format, ...$values) . PHP_EOL);
    }

    private function checkMode(): int
    {
        return match ($this->currentDialect) {
            'http://json-schema.org/draft-06/schema#',
            'http://json-schema.org/draft-07/schema#' => Constraint::CHECK_MODE_NORMAL | Constraint::CHECK_MODE_STRICT,
            default => Constraint::CHECK_MODE_NORMAL,
        };
    }
}
