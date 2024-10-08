---
title: Obtu AI
emoji: 📸
colorFrom: red
colorTo: pink
sdk: docker
app_file: main.py
pinned: false
license: mit
models:
  - black-forest-labs/FLUX.1-dev
  - alvdansen/frosting_lane_flux
  - XLabs-AI/flux-RealismLora
  - alvdansen/softserve_anime
  - davisbro/half_illustration
  - Norod78/Flux_1_Dev_LoRA_Paper-Cutout-Style
  - linoyts/yarn_art_Flux_LoRA
  - kudzueye/Boreal
  - XLabs-AI/flux-lora-collection
  - martintomov/retrofuturism-flux
  - dataautogpt3/FLUX-SyntheticAnime
  - veryVANYA/ps1-style-flux
  - multimodalart/flux-tarot-v1
  - alfredplpl/flux.1-dev-modern-anime-lora
---
# ObtuAI - AI-Powered Image Generation Platform

ObtuAI is an innovative platform that leverages artificial intelligence to generate and manipulate images based on user prompts and custom models.

## Features
- Image generation using AI models
- Custom model training
- User authentication with Google
- Credit system for image generation and model training
- Stripe integration for purchasing credits

## Tech Stack
- Backend: FastAPI, Python
- Frontend: Gradio
- Database: Supabase
- Authentication: Google OAuth
- Payment Processing: Stripe
- AI Models: Replicate

## Setup Instructions

1. Clone the repository

2. Install the dependencies
```bash
pip install -r requirements.txt
```

3. Rename the `.env.example` file to `.env` and fill in the required environment variables

4. Run the FastAPI server

```bash
uvicorn main:app --reload
```

The application will be available at http://127.0.0.1:8000.

## Stripe Local Testing

Run webhook locally for testing (Put your stripe on test mode and get the keys)
The code above will generate the code for the webhook

```bash
stripe listen --forward-to http://127.0.0.1:7000/webhook
```

### Use the following test card
- Name: Any
- Number: 4242 4242 4242 4242
- CVC: 123
- Date: Any future date