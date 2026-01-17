# OBS Assets Directory

This directory contains media assets for OBS Studio streaming:

## Directory Structure

- **Avatar Images**: Character emotion sprites (立ち絵)
  - `avatar_neutral.png` - Default neutral expression
  - `avatar_happy.png` - Happy expression
  - `avatar_sad.png` - Sad expression
  - `avatar_angry.png` - Angry expression
  
- **Background Images**: Stream backgrounds
  - `background.png` - Main background image

## Image Specifications

- **Format**: PNG with transparency support recommended
- **Resolution**: 1920x1080 (Full HD) for backgrounds
- **Avatar**: Recommended 800x1200 to 1000x1500 for character sprites

## Usage

These assets are mounted read-only into the OBS Studio container at `/app/assets`.
The `body-desktop` service controls which avatar image is displayed based on the AI's emotional state.
