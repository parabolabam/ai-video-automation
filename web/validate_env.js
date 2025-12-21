#!/usr/bin/env node
/**
 * Environment variable validation for Next.js frontend.
 * Fails container startup if required environment variables are missing.
 */

const REQUIRED_VARS = [
  'NEXT_PUBLIC_API_URL',
  'NEXT_PUBLIC_SUPABASE_URL',
  'NEXT_PUBLIC_SUPABASE_ANON_KEY',
];

function validateEnv() {
  console.log('='.repeat(60));
  console.log('Frontend Environment Variable Validation');
  console.log('='.repeat(60));

  const missing = [];

  for (const varName of REQUIRED_VARS) {
    const value = process.env[varName];
    if (!value || value.trim() === '') {
      missing.push(varName);
    }
  }

  if (missing.length > 0) {
    console.log('\n❌ MISSING REQUIRED ENVIRONMENT VARIABLES:');
    missing.forEach(varName => {
      console.log(`   - ${varName}`);
    });
    console.log('\nContainer startup will FAIL.');
    console.log('Please set these environment variables and try again.');
    console.log('='.repeat(60));
    console.log('\n💥 Environment validation FAILED!');
    process.exit(1);
  }

  console.log('\n✅ All required environment variables are set.');
  console.log('\nCurrent Configuration:');
  console.log('='.repeat(60));

  for (const varName of REQUIRED_VARS) {
    const value = process.env[varName];
    // Mask sensitive values
    let masked;
    if (value.length > 10) {
      masked = value.substring(0, 4) + '*'.repeat(value.length - 8) + value.substring(value.length - 4);
    } else {
      masked = '*'.repeat(value.length);
    }
    console.log(`  ${varName}: ${masked}`);
  }

  console.log('='.repeat(60));
  console.log('\n✅ Environment validation PASSED!');
  console.log('Starting Next.js server...\n');
}

validateEnv();
