---
title: Job Search Copilot
date: 2026-11-20
section: projects
tags: [ai, python, llm, rag, agents, building]
visibility: public
summary: A personal project to make job searching a little easier while learning how AI agents work.
---

*A personal project to make job searching a little easier while learning how AI agents work.*

**Status:** Early development

## How It Started

While looking for my next role, I found myself spending quite a bit of time going through job descriptions, comparing them with my experience, and deciding which positions were worth applying for.

At the same time, I had started learning about AI agents and wanted to go beyond tutorials and small examples.

I thought, why not combine the two?

The idea was to build something that could compare my CV with a job description, highlight where my experience matched, point out possible gaps, and eventually help with some of the repetitive work involved in searching and applying for jobs.

This gave me a real problem to work on while exploring AI, rather than building something just for the sake of using new technology.

## What It Does

The project is still in its early stages.

The current version is a Python command-line tool that can:

- Compare a CV with a job description using keyword matching.
- Show matched and missing terms along with a basic fit score.
- Store CV information and interview stories in JSON files.
- Keep track of job applications and their status using a local SQLite database.

It's a starting point rather than a complete job-search assistant.

## How It's Built

I started with **Python**, keeping the application simple and running locally.

The current implementation uses:

- **Python CLI:** To run comparisons and manage applications.
- **Keyword-based matching:** To identify overlapping and missing terms between a CV and job description.
- **JSON:** To store CV information and interview examples.
- **SQLite:** To maintain a basic record of job applications.

I deliberately started without building a web interface or introducing AI agents immediately.

The idea was to establish a working base and then explore where LLMs, retrieval and agents would actually improve the results.

## Interesting Decisions and Challenges

**Starting with simple matching**

The first version uses keywords rather than an LLM.

It's a useful starting point, but the limitations are quite clear. Two descriptions can mean the same thing while using very different words.

Similarly, a high keyword match doesn't necessarily mean someone is suitable for a role.

This is one of the problems I want to explore further using semantic matching and LLMs.

**Separating facts from generated suggestions**

One thing I want to be careful about is the difference between what my CV actually says and what an AI model might infer.

For example, the tool should be able to suggest how I could present relevant experience, but it shouldn't invent skills or achievements.

This is an important consideration as I explore AI-generated CV suggestions and application assistance.

**Keeping personal data local**

CVs and application records contain personal information. For now, the application works with local files and a local database.

The public repository contains sample information rather than my actual CV and application history.

## Building with AI

I've been using ChatGPT and Claude Code while working on this project.

ChatGPT has helped me think through the problem, discuss possible approaches and understand concepts around LLMs, embeddings, retrieval and agents.

Claude Code has helped with implementation and experimentation.

I'm also learning where AI actually adds value and where a simpler piece of code might be enough.

That's one of the things I find interesting about this project. The application itself is intended to use AI, while I'm also using AI tools to build and learn from it.

## What I Learned

So far, this project has helped me think more carefully about the difference between simple automation and AI-driven workflows.

It has also made me realise how important it is to define what a useful result actually looks like.

A fit score alone isn't particularly helpful if I can't understand why a role was considered suitable or unsuitable.

I'd rather build something that explains the matches, gaps and reasoning, and lets me make the final decision.

## Where It Stands

The initial command-line application is in place.

I'm continuing to explore how to extend it with LLM-based analysis, embeddings, retrieval and eventually agent workflows that can use tools to carry out specific tasks.

Some possibilities I'm interested in are comparing requirements with relevant experience, suggesting improvements to CV wording, and helping track job opportunities.

These are areas I want to experiment with, not features I'm claiming are already complete.

The goal is to build something useful for my own job search while understanding the possibilities and limitations of AI agents.

**Links**

- <a href="https://github.com/mehulp/job-copilot" target="_blank" rel="noopener">View the code on GitHub</a>
- Write-up of one step of the build: [Copilot 4: meaning, not keywords](../journal/copilot-4-meaning-not-keywords.md)
