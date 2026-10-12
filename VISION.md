# The Local AI Stack — Project Vision

## What We're Building

A community-driven reference resource that answers one question for anyone running AI on their own hardware:

**"What should I run, on what I have, for what I need?"**

That's it. That's the whole thing. Everything else — the website, the guides, the data pipeline, the forum thread — exists to answer that question as clearly, completely, and accessibly as possible.

## Where It Came From

This started as a forum post on Level1Techs — a community of people who build, break, and optimize hardware for a living. The post was a table: "here are good models, organized by how much video memory your graphics card has." 

People started replying. Not with thanks — with *data*. "I run this on my AMD card and get this speed." "This model is nuts for coding." "Here's my 1-terabyte-RAM translation rig." "The new quant format is the golden ticket." The thread became a living collection of real-world experience that no benchmark website could replicate, because it came from people actually *using* these things in their daily work.

The table became a matrix. The matrix became a project. The project became **The Local AI Stack**.

## Who It's For

- The person with a $300 graphics card who wants to know if they can run a useful AI at home
- The developer with a workstation who wants the best coding model that fits their setup
- The homelab enthusiast building a multi-GPU rig and wondering what to put on it
- The researcher running niche workloads (historical document translation, security analysis) on unusual hardware
- The person who just wants to chat with a local AI and doesn't care about the details
- The person who cares *deeply* about the details and wants to compare every option

If you're running AI on hardware you own, this is for you.

## What Makes It Different

**It's community-sourced, not lab-benchmarked.** Every data point comes from a real person running a real setup doing real work. Not a synthetic benchmark. Not a press release. "I ran this for three weeks and here's what actually happened."

**It's organized by YOUR hardware, not by model name.** You don't search for "Qwen 3.8." You search for "I have a 24GB card" or "I have 128GB of RAM and one GPU." The resource meets you where you are.

**It covers the full stack.** Not just "which model" but "which model, in which file format, quantized which way, run by which software, on which hardware, configured how." The whole chain from silicon to sentence.

**It's honest about tradeoffs.** Every recommendation comes with context. "This is fast but uses a lot of power." "This fits your card but you'll lose context length." "This is the best quality but you need two GPUs." No hype. No vendor spin. Just the reality of what fits where.

**It evolves with the field.** The local AI space changes weekly. New models drop. New quant formats appear. New inference engines show up. The resource updates. The changelog tracks it. Nothing goes stale silently.

## The Components (and Why They Exist)

### The Forum Thread (Level1Techs)
**The conversation.** This is where people submit data, ask questions, debate choices, and build the community. It's the source of truth. It's where the human element lives. You can't replicate a forum's energy on a website.

### The Website (GitHub Pages)
**The reference.** This is where the data goes to live permanently, organized, filterable, searchable. It's the thing you bookmark. It's the thing you show a friend. It doesn't require a forum account. Anyone on the internet can use it. It's the "go to" resource.

### The Guides
**The education.** The data tells you *what* to run. The guides tell you *why* and *how*. What is quantization? Why does my model need so much memory? What's the difference between these two file formats? Why does my AMD card need different software than my NVIDIA card? The guides make the resource self-sufficient — you don't need to already be an expert to use it.

### The Data Pipeline (Python tools)
**The maintenance.** The glue that keeps everything current. Pulls new data from the forum, organizes it, generates the website. The maintainer's weekly workflow. Boring, reliable, automatable.

## The Philosophy

**Community owns the data. The maintainer organizes it.**

This isn't one person's opinion about the best models. It's a collection of many people's experiences, organized so you can find what's relevant to *you*. The maintainer's job is curation, not authorship. They don't decide what's best — they decide what's *organized* and *accessible*.

**The forum is the heart. The website is the brain.**

Conversation, debate, new data, human connection — that lives in the forum. Structure, search, reference, education — that lives on the website. They feed each other. The forum generates the data. The website makes the data usable. The website drives traffic back to the forum. The forum generates more data.

**Meet people where they are.**

Some people want a one-click app. Some want to tune every parameter. Some have a laptop. Some have a server rack. Some want to code. Some want to write novels. Some want to translate 2000-year-old documents. The resource serves all of them. The "Start Here" path gets a newcomer oriented in 30 seconds. The deep guides give an expert the detail they need. The matrix gives a comparer the side-by-side they want.

**The field moves. We move with it.**

A quant format that didn't exist last month is "the golden ticket" this month. A new inference engine makes 125B models run on a single consumer GPU. The resource doesn't pretend to be permanent. It has a changelog. It has version numbers. It acknowledges that what's true today may be superseded next month. That's honest. That's useful.

## The Success Metric

Not traffic. Not pageviews. Not SEO rankings.

**The moment someone says "oh, I would have spent weeks figuring that out" after spending ten minutes with the resource.**

The moment a newcomer with a single graphics card knows exactly what to download, how to run it, and what to expect — without reading forty forum threads and three YouTube videos first.

The moment someone with an unusual setup (four AMD cards, a terabyte of RAM, a Mac Studio) sees their configuration represented and validated. "Someone else is doing this. Here's how it works. Here are the tradeoffs."

That's the win.

## What This Is NOT

- Not a benchmark website. We don't run models. People do.
- Not a model recommendation service. We don't say "buy this." We say "here's what works on what you have."
- Not a vendor evaluation. We don't rank companies. We rank configurations.
- Not an academic paper. We cite community experience, not research labs.
- Not static. It changes. Weekly. Sometimes daily.

## The Name

**The Local AI Stack.**

"Local" because it's on your hardware. Your electricity. Your privacy. Your rules.

"AI" because it's broader than just language models. It's the whole local intelligence ecosystem.

"Stack" because it's layers. Hardware at the bottom. Inference engine in the middle. Model and quant on top. Your use case at the very top. You build your stack. We help you know what goes where.

---

*Documented from the MadGoat × AI collaboration, October 2026.*
*The Local AI Stack is a community project originating from Level1Techs.*
