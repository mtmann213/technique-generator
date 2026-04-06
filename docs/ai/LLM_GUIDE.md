# Working with the Local AI Assistant (LCC)

## Overview

TechniqueMaker includes an air-gapped local AI coding assistant for development on offline target machines.

## Components

- **Engine**: `llama.cpp` (`llama-server`) running on port `8000`
- **Model**: `Qwen2.5-Coder-7B-Instruct-GGUF` (recommended for C++ work)
- **Interface**: `lcc` (Local Claude Code) script for terminal-based interaction

## Setup on Air-Gapped Machine

1. Transfer `sidekiq_ai_bundle/` to the target via USB
2. Start the local server:
   ```bash
   cd sidekiq_ai_bundle/build/bin
   ./llama-server -m /path/to/qwen2.5-coder-7b.Q4_K_M.gguf \
     --host 127.0.0.1 --port 8000 --ctx-size 8192
   ```
3. Use the `lcc` script to interact:
   ```bash
   ./lcc "Why is my DMA alignment failing?"
   ```

## Piping Errors to LLM

```bash
# Pipe build errors directly to the local assistant
make soapy 2>&1 | ./lcc

# Or with context
./lcc "$(cat techniquemaker.log | tail -50)"
```

## Handover Document

For detailed context on architecture, recent hurdles, and solutions, see `LLM_HANDOVER_DOCUMENT.md` in the project root.

