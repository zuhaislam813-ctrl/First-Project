import { NextResponse } from 'next/server';

export async function GET() {
  // Sample products relevant to the AI Text-to-Audio SaaS
  const products = [
    {
      id: 'prod_starter',
      name: 'Starter Voice Pack',
      description: 'Includes 5 standard AI voices and up to 10 hours of text-to-speech generation per month.',
      price: 9.99,
      currency: 'USD',
      features: ['5 Standard Voices', '10 Hours Generation', 'MP3 Downloads']
    },
    {
      id: 'prod_pro',
      name: 'Pro Creator Pack',
      description: 'Unlock 20 premium ultra-realistic voices and 50 hours of audio generation.',
      price: 29.99,
      currency: 'USD',
      features: ['20 Premium Voices', '50 Hours Generation', 'WAV & MP3 Downloads', 'Commercial Rights']
    },
    {
      id: 'prod_enterprise',
      name: 'Enterprise Studio',
      description: 'Unlimited audio generation, voice cloning capabilities, and priority API access.',
      price: 99.99,
      currency: 'USD',
      features: ['Unlimited Generation', 'Voice Cloning', 'API Access', '24/7 Support']
    }
  ];

  return NextResponse.json(products);
}
