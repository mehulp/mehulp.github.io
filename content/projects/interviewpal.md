---
title: InterviewPal
section: projects
date: 2026-11-20
tags: [javascript, ai, building]
visibility: public
summary: Practising interview answers, one question at a time.
---

*Practising interview answers, one question at a time.*

**Status:** Working application, with ongoing improvements

## How It Started

While preparing for interviews, I spent a lot of time reading questions, writing answers and going through my notes.

But I realised that knowing an answer and explaining it clearly in an interview are two different things.

Sometimes I knew what I wanted to say, but struggled to organise my thoughts or finish my answer within a reasonable time.

I wanted a way to practise speaking through my answers regularly, without needing someone else to conduct a mock interview every time.

That's how InterviewPal started.

What began as a simple practice tool gradually grew into an application where I could rehearse interviews, record my answers and review how I was doing.

## What It Does

InterviewPal is a browser-based application that helps me practise for interviews.

It allows me to:

- Create and organise question sets for different topics.
- Practise through guided rehearsals or mock interviews.
- Answer questions by speaking or typing.
- Use timers to practise keeping answers within a reasonable length.
- Record and replay answers to see where I can improve.
- Review practice sessions and track progress.
- Get optional AI feedback on my answers.

The idea is to make interview preparation more practical, rather than just reading and memorising answers.

## How It's Built

I built InterviewPal using **HTML, CSS and JavaScript**.

This time I kept the architecture simple and decided not to use a backend. The application runs in the browser, with question sets, practice sessions and recordings stored locally.

It uses browser features such as:

- **Web Speech API** for speaking questions and recognising spoken answers.
- **MediaRecorder API** for recording and replaying responses.
- **Browser storage** for saving questions, settings and practice history.
- **Claude API** for optional AI-based feedback.

The application is hosted on GitHub Pages.

Keeping everything in the browser made it easier to build, deploy and use without maintaining a server. The trade-off is that saved information remains tied to the browser unless it's exported.

## Interesting Decisions and Challenges

**Making practice useful without AI**

I wanted InterviewPal to be useful even without an AI API key. Users can practise, record answers and review their sessions without using an LLM.

AI feedback is an additional feature, not something the application depends on.

**Getting speech and recording to work reliably**

Speech recognition and audio recording involve browser permissions and APIs that don't always behave consistently.

Handling microphone permissions, recognition failures and recording controls required more attention than I initially expected.

**Simplifying the interview experience**

As I added features, the application became more complicated to use.

I went through several rounds of changes to simplify the flow, from setting up an interview to answering questions and reviewing the session.

It was a good reminder that building a feature and making it easy to use are two different things.

## Building with AI

I used **ChatGPT and Claude Code** extensively while developing InterviewPal.

ChatGPT helped me discuss ideas, work through technical decisions and improve the interview flow. Claude Code helped with implementation, debugging and testing.

Most improvements came through repeated cycles of trying something, finding issues, discussing possible changes and testing again.

This has been an interesting experience in AI-assisted development, or vibe coding. It allowed me to experiment with unfamiliar technologies while still working through the design choices and understanding how the application behaves.

## What I Learned

This project taught me quite a bit about browser APIs, local storage and managing application state.

But one of the bigger lessons was around user experience.

A feature might work technically and still be frustrating to use. I found myself spending considerable time simplifying screens, removing unnecessary steps and making the overall experience more natural.

I also learned that AI-assisted development can speed things up, but reviewing and testing what gets built remains important.

## Where It Stands

InterviewPal is a working application that I continue to improve.

I've also connected it with [Study Hub](study-hub.md), allowing me to open interview practice from a learning plan and return to the plan afterwards.

I'm exploring ways to improve feedback quality and make practice sessions more useful over time.

For now, it serves the purpose for which I started building it: helping me practise regularly and become more comfortable explaining my thoughts in interviews.

**Links**

- <a href="https://mehulp.github.io/interview-pal/" target="_blank" rel="noopener">Try InterviewPal</a>
- <a href="https://github.com/mehulp/interview-pal" target="_blank" rel="noopener">View the code on GitHub</a>
