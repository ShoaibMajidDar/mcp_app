# MCP Client

## Overview

This client connects to the **MCP Server** using **Server-Sent Events (SSE)**. It is designed to interact with the server's tool that fetches and processes PDF files stored on OneDrive.

## How It Works

- The client establishes an SSE connection to the MCP Server.
- You need to provide your **OneDrive access token** and the **file ID** of the PDF document.
- The MCP Server uses this information to retrieve the file, generate a summary using the `gpt-4o-mini` model, and stream the response back to the client.

---

## Usage

1. Start the MCP Server (see its [README](https://github.com/ShoaibMajidDar/onedrive_mcp?tab=readme-ov-file#mcp-server) for setup).
2. Run the app using:
```bash
python3 app.py
```

---

## Requirements

- A valid OneDrive access token
- A file ID corresponding to a PDF document stored in your OneDrive account
- MCP Server running and accessible

---
