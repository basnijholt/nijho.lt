# 🎄🎁 Advent of Open Source – Day 22/24: tiller-streamlit 💰

(See my [intro post](https://www.linkedin.com/posts/basnijholt_advent-of-open-source-celebrating-activity-7269075513002909697-M89J))

Tracking personal finances is crucial, especially when working towards financial independence (see my WenFIRE post on Day 4). Today's project is `tiller-streamlit`, a Streamlit app that visualizes your financial data from Tiller. I host it on my local network under `money.local` using Traefik for easy access.

## 📖 Origin Story

* Used to use Intuit Mint, but when they shut down, I needed an alternative with full data control.
* Tiller automatically populates your financial data into a Google Sheet that you own forever.
* With 20+ accounts, manual updates are tedious – Tiller automates it.
* Combined Tiller's data with Streamlit's ease of use, creating a personal finance dashboard.

## 🔧 Technical Highlights

* Powered by Streamlit: Turns Python into a web app with minimal code.
* Tiller Integration: Connects to Tiller's Google Sheets for automated data retrieval.
* Interactive Visualizations: Uses Plotly and Altair for dynamic charts.
* Customizable Analysis: Filter by categories, time periods, and more.
* Net Worth Tracking: Calculates and visualizes net worth over time.
* Dockerized Deployment: Easy deployment with Docker, and served locally with Traefik.

## 📊 Impact

* Primarily for personal use, it has significantly improved my understanding of my finances.
* Great way to learn Streamlit and explore its capabilities.
* Visualizing spending patterns helps identify areas to cut back and make informed financial decisions on the path to financial independence.

## 🎯 Challenges and Solutions

* Learning Streamlit: Excellent documentation and community support made it a smooth process.
* Data Wrangling: Transforming Tiller's raw data into a format suitable for visualization.
* Deployment: Docker and Traefik simplified local deployment, making it accessible on my home network.

## 💡 Lessons Learned

* Data Ownership Matters: Owning your financial data gives you control and flexibility.
* Visualization is Key: Seeing your finances visually makes a huge difference.
* Streamlit is Powerful: Simplifies web app development.
* Automation is Essential: Tiller's automatic data population makes the whole process sustainable.
* Docker and Traefik Simplify Local Deployment: Making it easy to access the app on my home network.

## 🔮 Future Plans

* Budgeting Features: Integrate budget tracking and forecasting.
* Goal Setting: Set financial goals and track progress.
* Investment Tracking: Incorporate investment data for a complete picture.

Want to visualize your own finances with Tiller and Streamlit? Check out `tiller-streamlit` on GitHub ([https://github.com/basnijholt/tiller-streamlit](https://github.com/basnijholt/tiller-streamlit))!

#OpenSource #Python #Streamlit #PersonalFinance #DataVisualization #Tiller #Traefik #Docker