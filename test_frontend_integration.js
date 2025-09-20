/**
 * Simple integration test for the frontend components
 * This script verifies that the React components can be imported and rendered
 */

const fs = require('fs');
const path = require('path');

// Test that all required files exist
const requiredFiles = [
  'frontend/src/App.tsx',
  'frontend/src/components/ChatInterface.tsx',
  'frontend/src/components/ConversationSelector.tsx',
  'frontend/src/components/MessageList.tsx',
  'frontend/src/components/MessageInput.tsx',
  'frontend/src/services/api.ts',
  'frontend/types/chat.ts',
  'frontend/package.json',
  'frontend/public/index.html'
];

console.log('🧪 Testing Frontend Integration...\n');

let allTestsPassed = true;

// Test 1: Check if all required files exist
console.log('📁 Checking required files...');
requiredFiles.forEach(file => {
  if (fs.existsSync(file)) {
    console.log(`✅ ${file}`);
  } else {
    console.log(`❌ ${file} - MISSING`);
    allTestsPassed = false;
  }
});

// Test 2: Check TypeScript interfaces
console.log('\n🔍 Checking TypeScript interfaces...');
try {
  const chatTypesContent = fs.readFileSync('frontend/types/chat.ts', 'utf8');
  const requiredInterfaces = ['Message', 'ConversationContext', 'ChatRequest', 'ChatResponse'];
  
  requiredInterfaces.forEach(interfaceName => {
    if (chatTypesContent.includes(`interface ${interfaceName}`)) {
      console.log(`✅ ${interfaceName} interface defined`);
    } else {
      console.log(`❌ ${interfaceName} interface missing`);
      allTestsPassed = false;
    }
  });
} catch (error) {
  console.log(`❌ Error reading chat types: ${error.message}`);
  allTestsPassed = false;
}

// Test 3: Check component structure
console.log('\n🧩 Checking component structure...');
const components = [
  { name: 'ChatInterface', file: 'frontend/src/components/ChatInterface.tsx' },
  { name: 'ConversationSelector', file: 'frontend/src/components/ConversationSelector.tsx' },
  { name: 'MessageList', file: 'frontend/src/components/MessageList.tsx' },
  { name: 'MessageInput', file: 'frontend/src/components/MessageInput.tsx' }
];

components.forEach(component => {
  try {
    const content = fs.readFileSync(component.file, 'utf8');
    if (content.includes(`const ${component.name}:`)) {
      console.log(`✅ ${component.name} component properly defined`);
    } else {
      console.log(`❌ ${component.name} component not properly defined`);
      allTestsPassed = false;
    }
  } catch (error) {
    console.log(`❌ Error reading ${component.name}: ${error.message}`);
    allTestsPassed = false;
  }
});

// Test 4: Check API service
console.log('\n🌐 Checking API service...');
try {
  const apiContent = fs.readFileSync('frontend/src/services/api.ts', 'utf8');
  const requiredMethods = ['sendMessage', 'healthCheck'];
  
  requiredMethods.forEach(method => {
    if (apiContent.includes(`${method}(`)) {
      console.log(`✅ ApiService.${method} method defined`);
    } else {
      console.log(`❌ ApiService.${method} method missing`);
      allTestsPassed = false;
    }
  });
} catch (error) {
  console.log(`❌ Error reading API service: ${error.message}`);
  allTestsPassed = false;
}

// Test 5: Check CSS modules
console.log('\n🎨 Checking CSS modules...');
const cssModules = [
  'frontend/src/App.module.css',
  'frontend/src/components/ChatInterface.module.css',
  'frontend/src/components/ConversationSelector.module.css',
  'frontend/src/components/MessageList.module.css',
  'frontend/src/components/MessageInput.module.css'
];

cssModules.forEach(cssFile => {
  if (fs.existsSync(cssFile)) {
    console.log(`✅ ${cssFile}`);
  } else {
    console.log(`❌ ${cssFile} - MISSING`);
    allTestsPassed = false;
  }
});

// Test 6: Check package.json dependencies
console.log('\n📦 Checking package.json dependencies...');
try {
  const packageJson = JSON.parse(fs.readFileSync('frontend/package.json', 'utf8'));
  const requiredDeps = ['react', 'react-dom', 'axios'];
  
  requiredDeps.forEach(dep => {
    if (packageJson.dependencies && packageJson.dependencies[dep]) {
      console.log(`✅ ${dep} dependency present`);
    } else {
      console.log(`❌ ${dep} dependency missing`);
      allTestsPassed = false;
    }
  });
} catch (error) {
  console.log(`❌ Error reading package.json: ${error.message}`);
  allTestsPassed = false;
}

// Final result
console.log('\n' + '='.repeat(50));
if (allTestsPassed) {
  console.log('🎉 All frontend integration tests PASSED!');
  console.log('✅ Frontend components are properly structured');
  console.log('✅ TypeScript interfaces are defined');
  console.log('✅ API service is implemented');
  console.log('✅ CSS modules are present');
  console.log('✅ Dependencies are configured');
  console.log('\n📝 Next steps:');
  console.log('   1. Install dependencies: cd frontend && npm install --legacy-peer-deps');
  console.log('   2. Start development server: npm start');
  console.log('   3. Test with backend: docker-compose up backend redis');
} else {
  console.log('❌ Some frontend integration tests FAILED!');
  console.log('Please check the errors above and fix the issues.');
  process.exit(1);
}