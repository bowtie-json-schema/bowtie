from importlib import metadata
from pathlib import Path
import json

from attrs import define, field
from lsprotocol.types import (
    TEXT_DOCUMENT_DID_CHANGE,
    TEXT_DOCUMENT_DID_OPEN,
    WORKSPACE_DID_CHANGE_CONFIGURATION,
    Diagnostic,
    DiagnosticSeverity,
    DidChangeConfigurationParams,
    DidChangeTextDocumentParams,
    DidCloseTextDocumentParams,
    DidOpenTextDocumentParams,
    Position,
    Range,
)
from pygls.server import LanguageServer

from bowtie._commands import Test, TestCase


def _validate(ls, params):
    document = ls.workspace.get_document(params.text_document.uri)

    try:
        instance = json.loads(document.source)
        schema_path = instance.get("$schema")
        if schema_path is None:
            return

        schema = json.loads(Path(schema_path).read_text())
    except json.JSONDecodeError as error:
        line = error.lineno - 1
        col = error.colno - 1
        diagnostics = [
            Diagnostic(
                range=Range(
                    start=Position(line=line, character=col),
                    end=Position(line=line, character=col + 1),
                ),
                message=error.msg,
                severity=DiagnosticSeverity.Error,
                source=ls.name,
            ),
        ]
    else:
        case = TestCase(
            description="bowtie validate",
            schema=schema,
            tests=[Test(description="", instance=instance)],
        )

        import jsonschema.validators

        validator = jsonschema.validators.validator_for(schema)(schema)
        diagnostics = [
            Diagnostic(
                range=Range(
                    start=Position(line=0, character=0),
                    end=Position(line=0, character=1),
                ),
                message=error.message,
                severity=DiagnosticSeverity.Error,
                source=ls.name,
            )
            for error in validator.iter_errors(instance)
        ]

    ls.publish_diagnostics(document.uri, diagnostics)


@define
class Bowtie:
    """
    A Bowtie-based language server.
    """

    _ls: LanguageServer = field(alias="ls")

    @classmethod
    def create(cls):
        ls = LanguageServer(
            name="bowtie-ls",
            version=metadata.version("bowtie-json-schema"),
        )

        @ls.feature(WORKSPACE_DID_CHANGE_CONFIGURATION)
        def did_change_configuration(
            ls, params: DidChangeConfigurationParams = None
        ):
            ls.show_message("HELLO")

        @ls.feature(TEXT_DOCUMENT_DID_CHANGE)
        def did_change(ls, params: DidChangeTextDocumentParams):
            _validate(ls, params)

        @ls.feature(TEXT_DOCUMENT_DID_OPEN)
        def did_open(ls, params: DidOpenTextDocumentParams):
            _validate(ls, params)

        return cls(ls=ls)

    def start(self):
        self._ls.start_io()
