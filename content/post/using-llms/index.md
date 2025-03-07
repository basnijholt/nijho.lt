---
title: "🧠 Optimizing My LLM Workflow: Self-Hosting AI Interfaces for Open Source Development"
subtitle: A practical guide to accessing powerful AI models through self-hosted interfaces
summary: How I leverage LibreChat, OpenWebUI, and various AI APIs to enhance my development workflow without subscriptions
projects: []
date: '2025-03-07T00:00:00Z'
draft: false
featured: false

image:
  caption: 'Modern development workflow powered by AI'
  focal_point: ''
  placement: 2
  preview_only: false

authors:
  - admin

tags:
  - AI
  - LLM
  - OpenWebUI
  - LibreChat
  - Claude
  - GPT
  - Gemini
  - DeepSeek
  - Qwen
  - OpenRouter
  - self-hosting
  - docker
  - API
  - clip-files
  - cursor
  - workflow

categories:
  - AI
  - development
  - self-hosting
  - level:intermediate
---

# How I Use LLMs in My Daily Workflow

Over the past 1.5 years, I've developed a workflow for integrating Large Language Models into my daily life, particularly for open source software development.
I wanted to share my setup and recent discoveries that have improved my experience.
Setting it up takes a little technical know-how, but once it's up and running, using it is easy, even my spouse uses it!

## Starting with OpenWebUI

For most of the last year, I've relied on [OpenWebUI](https://openwebui.com/) as my primary interface for accessing various commercial LLMs:

- OpenAI's GPT-4o
- Anthropic's Claude 3.5
- Google's Gemini models

OpenWebUI is primarily designed for running local models, but it can work with remote APIs through what it calls ["functions"](https://openwebui.com/functions) - essentially Python modules that establish connections to these external APIs.
While functional, this approach requires additional setup and configuration to get working properly.

## Discovering LibreChat: A Game-Changer

Recently, I discovered [LibreChat](https://www.librechat.ai/), which has dramatically improved my LLM experience:

- **Speed**: Pages load in under a second, compared to 5-10 seconds with OpenWebUI.
This performance difference is especially noticeable when accessing either interface from my iPhone.
- **API Support**: Native integration with virtually all major AI company APIs you can think of, right out of the box
- **Convenience**: No need to implement custom Python functions - all popular models are supported by default
- **Reasoning Support**: LibreChat works much better with the new reasoning models, properly placing the reasoning part of replies in a dropdown.
The amount of reasoning tokens is also easily parameterized.

## The Rise of Free & Nearly-Free Powerful Models

The landscape has changed dramatically in just the last month.
Several extremely capable models are now either completely free or essentially free:

- **Google's [gemini-exp-1206](https://ai.google.dev/gemini-api/docs/models/experimental-models)**: Impressively capable with a huge context window for code
- **[DeepSeek](https://www.deepseek.com/)**: DeepSeek v3 is the best in this category, offering remarkable performance at minimal cost
- **[Qwen](https://qwen-ai.com/qwq-32b/)**: Another powerful option that won't break the bank

This democratization of access to high-quality models has been a game-changer for my development workflow.

## Claude 3.7: Worth Every Penny

My current go-to model is Anthropic's Claude 3.7.
I'm completely blown away by its capabilities and find myself happy to pay the premium price for what it delivers.
The quality of responses, understanding of complex contexts, and overall reliability have made it an indispensable tool in my workflow.

## OpenRouter: Hundreds of Models, One API

A game-changing discovery has been OpenRouter.ai.
With just one API key, I can access hundreds of different models, many of which are completely free to use.
This has dramatically expanded my toolkit without increasing costs.

## Easy Deployment with Docker Compose

Both OpenWebUI and LibreChat are extremely easy to deploy using Docker Compose.
As someone who self-hosts numerous services, I appreciate how straightforward it is to get either of these interfaces up and running with a simple docker-compose file.
This accessibility makes it easy for even those with limited server experience to set up their own LLM workstation.

## Why I Don't Run Local Models

Despite being a self-hosting enthusiast (I run over 50 services at home!), I've stuck with commercial API models for my work.
Since I mainly develop open source software, data privacy concerns are minimal—the code I work with is already publicly available.
The commercial models also provide superior performance for my specific needs.

## Avoiding Web Interfaces & Subscriptions

I deliberately avoid using ChatGPT or Claude through their native web interfaces.
Why? Simple economics.
By accessing these models through my own interfaces with API keys, I don't have to pay separate subscription fees (≈$20) for each service.
This consolidated approach saves money while providing more flexibility.

## Code Editor Experiments

I've tried [Cursor editor](https://www.cursor.com/), which offers an interesting AI-integrated coding experience.
While many features are impressive, I encountered limitations—particularly with the Python debugger, which is [a known issue](https://forum.cursor.com/t/python-debugger-doesnt-launch/1661/19).
Despite its promise, these limitations pushed me back to my custom workflow.

## My DIY Solution: clip-files

To compensate, I heavily rely on a CLI tool I created called "[clip-files](https://github.com/basnijholt/clip-files/)." This simple utility lets me pass filenames as arguments, and it copies their contents to my clipboard along with useful metadata.
This makes it effortless to share code with LLMs regardless of which interface I'm using—simple, fast, and effective.
Together with the [`zsh-autosuggestions`](https://github.com/zsh-users/zsh-autosuggestions) plugin–which I talked about in [another post](../terminal-ninja/)–generating the right prompt is a breeze.

## My Current Setup

Today, I maintain access to multiple top-tier models through LibreChat's interface and OpenRouter.ai's API.
This gives me flexibility to choose the right model for specific tasks while enjoying a responsive, feature-rich environment without unnecessary subscription costs.

For fellow self-hosters and developers looking to optimize their LLM workflow, I highly recommend this combination, especially if you're currently using web interfaces or struggling with OpenWebUI's performance.

What LLM setups are you using in your workflow? I'd love to hear about your experiences in the comments!

# How I Use LLMs in My Daily Workflow

Over the past year, I've developed a workflow for integrating Large Language Models into my daily life, particularly for open source software development.
I wanted to share my setup and recent discoveries that have improved my experience.

## Starting with OpenWebUI

For most of the last year, I've relied on [OpenWebUI](https://openwebui.com/) as my primary interface for accessing various commercial LLMs:

- OpenAI's GPT-4o
- Anthropic's Claude 3.5
- Google's Gemini models

OpenWebUI is primarily designed for running local models, but it can work with remote APIs through what it calls "functions" - essentially Python modules that establish connections to these external APIs.
While functional, this approach requires additional setup and configuration to get working properly.

## Discovering LibreChat: A Game-Changer

Recently, I discovered [LibreChat](https://www.librechat.ai/), which has dramatically improved my LLM experience:

- **Speed**: Pages load in under a second, compared to 5-10 seconds with OpenWebUI.
This performance difference is especially noticeable when accessing either interface from my iPhone.
- **API Support**: Native integration with virtually all major AI company APIs you can think of, right out of the box
- **Convenience**: No need to implement custom Python functions - all popular models are supported by default

## The Rise of Free & Nearly-Free Powerful Models

The landscape has changed dramatically in just the last month.
Several extremely capable models are now either completely free or essentially free:

- **Google's [gemini-exp-1206](https://ai.google.dev/gemini-api/docs/models/experimental-models)**: Impressively capable with a huge context window for code
- **[DeepSeek](https://www.deepseek.com/)**: DeepSeek v3 is the best in this category, offering remarkable performance at minimal cost
- **[Qwen](https://qwen-ai.com/qwq-32b/)**: Another powerful option that won't break the bank

This democratization of access to high-quality models has been a game-changer for my development workflow.

## Claude 3.7: Worth Every Penny

My current go-to model is Anthropic's Claude 3.7.
I'm completely blown away by its capabilities and find myself happy to pay the premium price for what it delivers.
The quality of responses, understanding of complex contexts, and overall reliability have made it an indispensable tool in my workflow.

## OpenRouter: Hundreds of Models, One API

A game-changing discovery has been OpenRouter.ai.
With just one API key, I can access hundreds of different models, many of which are completely free to use.
This has dramatically expanded my toolkit without increasing costs.

## Easy Deployment with Docker Compose

Both OpenWebUI and LibreChat are extremely easy to deploy using Docker Compose.
As someone who self-hosts numerous services, I appreciate how straightforward it is to get either of these interfaces up and running with a simple docker-compose file.
This accessibility makes it easy for even those with limited server experience to set up their own LLM workstation.

## Why I Don't Run Local Models

Despite being a self-hosting enthusiast (I run over 50 services at home!), I've stuck with commercial API models for my work.
Since I mainly develop open source software, data privacy concerns are minimal—the code I work with is already publicly available.
The commercial models also provide superior performance for my specific needs.

## Avoiding Web Interfaces & Subscriptions

I deliberately avoid using ChatGPT or Claude through their native web interfaces.
Why? Simple economics.
By accessing these models through my own interfaces with API keys, I don't have to pay separate subscription fees for each service.
This consolidated approach saves money while providing more flexibility.

## Code Editor Experiments

I've tried [Cursor editor](https://www.cursor.com/), which offers an interesting AI-integrated coding experience.
While many features are impressive, I encountered limitations—particularly with the Python debugger, which is a known issue.
Despite its promise, these limitations pushed me back to my custom workflow.

## My DIY Solution: clip-files

To compensate, I heavily rely on a CLI tool I created called "[clip-files](https://github.com/basnijholt/clip-files/)." This simple utility lets me pass filenames as arguments, and it copies their contents to my clipboard along with useful metadata.
This makes it effortless to share code with LLMs regardless of which interface I'm using—simple, fast, and effective.

## My Current Setup

Today, I maintain access to multiple top-tier models through LibreChat's interface and OpenRouter.ai's API.
This gives me flexibility to choose the right model for specific tasks while enjoying a responsive, feature-rich environment without unnecessary subscription costs.

For fellow self-hosters and developers looking to optimize their LLM workflow, I highly recommend this combination, especially if you're currently using web interfaces or struggling with OpenWebUI's performance.

What LLM setups are you using in your workflow? I'd love to hear about your experiences in the comments!
