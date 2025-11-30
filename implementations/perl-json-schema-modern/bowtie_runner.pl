#!/usr/bin/perl

use strict;
use warnings;

use JSON::Schema::Modern;
use Mojo::JSON qw(decode_json encode_json false true);
use Try::Tiny;

my %dialect = (
    'https://json-schema.org/draft/2020-12/schema' => 'draft2020-12',
    'https://json-schema.org/draft/2019-09/schema' => 'draft2019-09',
    'http://json-schema.org/draft-07/schema#'      => 'draft7',
    'http://json-schema.org/draft-06/schema#'      => 'draft6',
    'http://json-schema.org/draft-04/schema#'      => 'draft4',
);

my $started = 0;
my $schema;
my $os = qx/uname/;
chomp $os;
my $os_version = qx/uname -r/;
chomp $os_version;

my %cmds = (
    start => sub () {
        my $request = shift;
        die 'Wrong version!' unless $request->{version} == 1;
        $started = 1;
        return {
            version        => 1,
            implementation => {
                language => 'perl',
                name     => 'JSON-Schema-Modern',
                version  => $JSON::Schema::Modern::VERSION,
                homepage => 'https://metacpan.org/release/JSON-Schema-Modern/',
                issues   =>
                  'https://github.com/karenetheridge/JSON-Schema-Modern/issues',
                source =>
                  'https://github.com/karenetheridge/JSON-Schema-Modern',
                dialects         => [ keys %dialect ],
                os               => $os,
                os_version       => $os_version,
                language_version => $^V,
            },
        };
    },
    dialect => sub () {
        my $request = shift;
        die 'Not started!' unless $started;
        if ( exists $dialect{ $request->{dialect} } ) {
            $schema = $dialect{ $request->{dialect} };
            return { ok => true };
        }
        else {
            return { ok => false };
        }
    },
    run => sub () {
        my $request = shift;
        die 'Not started!' unless $started;
        my $js = JSON::Schema::Modern->new( specification_version => $schema );
        my $case = $request->{case};
        while ( my ( $url, $content ) = each %{ $case->{registry} } ) {
            try {
                $js->add_schema( $url, $content );
            }
            catch {
                return {
                    errored => true,
                    seq     => $request->{seq},
                    context => { traceback => $_ },
                };
            };
        }
        my @results = ();
        foreach my $test ( @{ $case->{tests} } ) {
            try {
                push @results,
                  $js->evaluate( $test->{instance}, $case->{schema} );
            }
            catch {
                return {
                    errored => true,
                    seq     => $request->{seq},
                    context => { traceback => $_ },
                };
            };
        }
        return {
            seq     => $request->{seq},
            results => \@results,
        };
    },
    stop => sub () {
        die 'Not started!' unless $started;
        exit;
    },
);

local $| = 1;    # autoflush
while (<>) {
    my $request  = decode_json($_);
    my $response = $cmds{ $request->{cmd} }($request);
    print encode_json($response), "\n";
}
