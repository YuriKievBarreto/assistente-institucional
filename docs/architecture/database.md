# Database

## Overview

The project uses two databases with distinct responsibilities:

- **Qdrant** — vector database responsible for semantic search over IFPB institutional documents
- **PostgreSQL** — relational database responsible for users, chat sessions, and message history

## Why two databases?

Qdrant is specialized in vector similarity search, which is the core of the RAG pipeline.
PostgreSQL handles the application's relational data, where structured queries and referential
integrity matter more than semantic search.

Keeping responsibilities separate avoids the need for extensions like pgvector, which would add
complexity to PostgreSQL with no real benefit given that Qdrant is already in the stack.

## Relational modeling

### Design decisions

- UUIDs as primary keys across all tables — avoids exposing sequential IDs in the API
- Soft delete via `deleted_at` on `users`, `chats`, and `messages` — preserves history for analysis
- Authentication isolated in `user_accounts` — allows multiple providers (local, Google)
  per user without nullable columns in the main table
- `messages.content` as `text` — no character limit for long messages

### Relationships

- `users` 1:N `user_accounts` — a user can have multiple authentication methods
- `users` 1:N `chats` — a user can have multiple chats
- `chats` 1:N `messages` — a chat can have multiple messages

### Diagram

![Database diagram](./database_diagram.png)

## ORM

SQLModel — unifies SQLAlchemy (database layer) and Pydantic (validation) in a single class
definition, avoiding model duplication between the data layer and the API.

