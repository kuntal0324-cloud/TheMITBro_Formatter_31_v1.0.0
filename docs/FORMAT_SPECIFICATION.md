# Formatter Specification

## Purpose

TheMITbro Formatter converts structured/raw examination questions into consistent publication artifacts.

## Supported publication outputs

- GitHub-compatible Markdown
- SVG diagram artifacts
- PDF question papers
- HTML question papers

## Mathematical normalization

The formatter normalizes supported LaTeX and Unicode mathematical notation while preserving ordinary prose. Examples include operator normalization, fractions, superscripts/subscripts, and common Unicode mathematical operators.

## Validation principle

Malformed or unsupported constructs must fail closed or remain explicitly unsupported. The formatter must not silently invent mathematical content.

## Determinism

For a fixed input and formatter contract, repeated compilation must produce byte-identical release artifacts wherever the artifact format permits deterministic serialization.
