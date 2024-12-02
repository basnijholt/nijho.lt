# 🎄🎁 Advent of Open Source – Day 2/24: Adaptive Lighting 💡

(See my [intro post](https://www.linkedin.com/posts/basnijholt_advent-of-open-source-celebrating-activity-7269075513002909697-M89J))

Unlike yesterday's Calendar of Life project, today we're looking at one of my most popular contributions. It's one of several Home Assistant and home automation related projects I'll be sharing this month. While my coding journey started in scientific computing with physics simulations, discovering how to control my home environment through code sparked a new obsession. Home Assistant, currently the **#1** open source project on GitHub, is the brain of my smart home and lets you control and automate everything from lights to thermostats, completely locally and privacy-focused.

Keep your lighting in sync with the sun, they said. It'll be simple, they said...

## 📖 Origin Story
Back in 2020, inspired by @claytonjn's circadian_lighting Home Assistant component, I wanted to create a more comprehensive solution for automatically adjusting lights based on the time of day. What started as a contribution attempt to Home Assistant Core evolved into its own custom component when the PR wasn't merged - handling all the edge cases made the code too complex for core. The standalone component gave us the freedom to implement features properly, becoming one of Home Assistant's most installed custom integrations.

## 🔧 Technical Highlights
While the concept is simple, making it work reliably is... interesting:
* Handles unreliable Zigbee networks and flaky WiFi connections
* Manages different light brands' quirks (looking at you, IKEA bulbs 👀)
* Provides smooth transitions between color temperatures
* Detects manual overrides without disrupting user control
* Supports sleep modes for bedtime routines
* Configurable via YAML or the UI (only integration to support this!)

The integration has 38 parameters to fine-tune your lighting. Try our [WebAssembly simulator](https://basnijholt.github.io/adaptive-lighting/) to visualize your settings!

## 📊 Impact
* 2000+ GitHub stars
* 103 contributors
* 512 issues
* Tens of thousands of active users
* Available in 20+ languages
* One of the most installed custom integrations
* Featured in several YouTube videos and podcasts
* Dedicated parameter visualization web app

## 🎯 Challenges We Solved
* Lights randomly turning on (bulbs falsely reporting state)
* Network congestion (solved with Zigbee grouping)
* Different brands interpreting colors differently
* Handling manual overrides gracefully

## 💡 Lessons Learned
1. "It works on my setup" is just the beginning
2. Users surprise you (like using it for plants, or above the polar circle!)
3. Edge cases multiply quickly
4. Documentation is as important as code
5. Open source thrives on community effort

Want your lights to follow the sun? Check out the [project on GitHub](https://github.com/basnijholt/adaptive-lighting) and try the [simulator](https://basnijholt.github.io/adaptive-lighting/)!

#OpenSource #HomeAssistant #SmartHome #IoT #Python