---
title: Study Hub
section: projects
date: 2026-11-20
tags: [python, fastapi, react, microservices]
visibility: public
summary: One place to organise my learning resources and keep track of what I'm studying.
---

*One place to organise my learning resources and keep track of what I'm studying.*

**Status:** Working application, with ongoing improvements

## How It Started

While preparing for technical and system design interviews, I was collecting articles, videos, tutorials and other learning resources.

Over time, these were scattered across browser bookmarks, notes and different applications. I often found myself searching for something I had already saved.

I wanted a simple way to organise these resources, group them by topic, and come back to them when needed.

Study Hub grew out of an earlier bookmark management project I had been experimenting with. As I started using it for my own interview preparation, the idea of turning it into a dedicated learning tool made more sense.

It also gave me a good opportunity to get back into hands-on development and revisit some of the architectural concepts I'd been working with as an Engineering Manager.

## What It Does

Study Hub lets me save and organise learning resources in one place.

I can:

- Save articles, videos and other links with notes and tags.
- Search and filter resources when I need them.
- Group resources into Learning Plans and track my progress.
- Create shared boards and invite others to view selected resources.
- Copy resources from shared boards into my own library.

The idea is fairly simple: spend less time searching for learning material and more time actually using it.

## How It's Built

I used **ChatGPT and Claude Code** throughout development.

**ChatGPT** helped me think through the requirements, architecture, technical decisions and trade-offs. **Claude Code** helped with implementation, testing, debugging and making changes to the code.

My focus was on understanding what we were building, reviewing the decisions, testing the application and learning from the process, rather than writing every line of code myself.

I used **Python and FastAPI** for the backend, **React and TypeScript** for the frontend, and **PostgreSQL** for data storage.

The backend is divided into five services:

- **Gateway:** A single entry point for API requests.
- **Auth:** Login, authentication and tokens.
- **Items:** Learning resources, tags and Learning Plans.
- **Board:** Shared boards and access permissions.
- **Connectors:** Integrations with external sources, currently not part of the active application flow.

Each service has its own responsibilities and database schema.

The application runs on Railway for the backend and Cloudflare Workers for the frontend.

For a personal learning application, a simpler architecture would certainly have worked. I deliberately chose multiple services because I wanted to work through service boundaries, authentication, communication and deployment in practice.

## Interesting Decisions and Challenges

**Deciding what should be a separate service**

One of the things I wanted to understand better was where to draw service boundaries.

For example, Learning Plans could have been a separate service, but they are closely related to the resources a user already owns. Keeping them together made more sense.

Sharing resources was different. It needed its own permissions and rules, so I kept that responsibility in the Board service.

**Handling authentication and permissions**

I wanted to explore the difference between identifying a user and deciding what that user is allowed to do.

The Gateway checks authentication, but the backend services also verify tokens independently. The Board service handles permissions such as who can manage a board and who can only view it.

This helped me work through authentication and role-based access control beyond just reading about them.

**Sharing resources without tightly coupling services**

When someone shares a resource, the Board service stores a copy of the information needed to display it.

This avoids repeatedly calling the Items service whenever another user opens the board. The trade-off is that changes to the original resource may not automatically appear in the shared copy.

It was a useful example of how even a small application can involve decisions around data ownership and consistency.

## What I Learned

The biggest learning wasn't any particular framework or technology.

It was working through the small decisions that come up while building an application: where a piece of functionality belongs, how services communicate, what happens when something fails, and whether the additional complexity is really justified.

I also got practical experience with building APIs, managing database changes, writing tests and deploying an application.

I've maintained an architecture and decision log alongside the code. Looking back at why I made a particular choice has been just as useful as writing the code itself.

## Where It Stands

Study Hub is deployed and usable. The main features around organising resources, Learning Plans and shared boards are working.

I'm continuing to improve it as part of my learning. One area I'm exploring is connecting Study Hub with [InterviewPal](interviewpal.md), so that learning resources and interview practice can be part of the same flow.

There's still room for improvement, but the application already serves the purpose for which I started building it.

**Links**

- <a href="https://study-hub.mehul-patankar.workers.dev/" target="_blank" rel="noopener">Try Study Hub</a>
- <a href="https://github.com/mehulp/study-hub" target="_blank" rel="noopener">View the code on GitHub</a>
