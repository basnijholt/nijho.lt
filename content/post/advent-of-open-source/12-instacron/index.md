---
title: "instacron 📸"
date: 2024-12-12
draft: false
featured: false
summary: "🎄🎁 Advent of Open Source – Day 12/24: Automating Instagram posting with random philosophical quotes and emojis, because why not?"
subtitle: "🎄🎁 Advent of Open Source – Day 12/24: A Python script for automated, humorous Instagram content generation."
tags:
  - open-source
  - python
  - automation
  - photography
  - instagram
  - advent
categories:
  - technology
  - open-source
  - advent
authors:
  - admin
excludeFromList: true
---

(See my [intro post](../))

Ever found yourself with beautiful photos but too lazy to post them? Instead of changing my habits, I did what any developer would do: spent way more time automating the process than it would have taken to post manually.

## 📖 Origin Story

Back in 2017, I had hundreds of landscape photos from traveling through South America that I wanted to share on Instagram. The solution? Write a Python script that would randomly select photos and post them automatically, complete with philosophical quotes randomly selected from Bukowski, Einstein, or Dostoevsky because... it seemed to be the default of all "influencers" at the time. Nothing says "authentic travel experience" like an auto-generated Bukowski quote about drinking next to your serene mountain photo!

{{< figure src="image_2.png" caption="Instacron Example Post" alt="Screenshot of an Instagram post with a person standing in a stone archway overlooking a sunset, captioned 'Taken in United States, Santa Barbara' with hashtags related to nature and travel." >}}

{{< figure src="image_3.png" caption="Instacron Example Post" alt="Screenshot of an Instagram post of a cave with a river flowing through it, captioned 'Taken in Thailand, some cave' with hashtags related to travel and adventure." >}}

{{< figure src="image_4.png" caption="Instacron Example Post" alt="Screenshot of an Instagram post showing a misty mountain landscape at sunrise, captioned 'Taken in Thailand-Laos border' with hashtags related to nature and travel." >}}

{{< figure src="image_5.png" caption="Instacron Example Post" alt="Screenshot of an Instagram post of a mountain range with a green field in the foreground, captioned 'Taken in Lago Argentino, SC, Argentina' with hashtags related to nature and travel." >}}


## 🔧 Technical Highlights

- Randomly selects photos from a directory
- Adds location data from EXIF metadata
- Generates captions with random philosophical quotes
- Adds two random emojis to match the "mood"
- Automatically generates relevant hashtags
- Tracks posting frequency
- Uses cron for scheduled posting

## 📊 Impact

- 21 GitHub stars
- 4143 Instagram followers
- Successfully posted hundreds of photos
- Generated some concerned DMs (more on that below!)

## 🎯 Challenges and Solutions

- Instagram's ever-changing API
- Handling rate limits and restrictions
- Ensuring photos weren't posted multiple times
- Making captions interesting without human input
- The delicate art of random emoji selection

## 😅 Funny Story

The random quote and emoji selector once created an unexpectedly dramatic post. Picture this: a beautiful landscape photo paired with a deeply philosophical quote about solitude, and topped with a broken heart emoji (💔). Within hours, I started receiving concerned DMs from friends asking if everything was okay and whether my relationship had ended!

I had to explain that no, I wasn't going through a breakup - my bot just had a flair for the dramatic! These occasional mismatches made the whole thing more entertaining.

## 💡 Lessons Learned

1. Sometimes the best projects come from pure laziness
2. Automation doesn't always save time, but it's fun
3. Never underestimate the power of a misplaced emoji to trigger concerned messages
4. Some followers actually care about you (even if they're worried about your bot-generated content)

While I haven't used this project in 6 years (Instagram's API changes eventually won), it remains a testament to the lengths we'll go to avoid repetitive tasks. Check out [instacron on GitHub](https://github.com/basnijholt/instacron)!

#OpenSource #Python #Automation #Photography #Instagram
