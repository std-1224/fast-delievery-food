#!/usr/bin/env python
"""
Test script to verify that login and registration functionality is working correctly.
Run this script to test the authentication system.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
import re


def test_login():
    """Test user login functionality"""
    print("Testing login functionality...")
    
    # Create a test client
    client = Client()
    
    # Get the login page
    response = client.get('/en/accounts/login/')
    if response.status_code != 200:
        print("❌ Login page not accessible")
        return False
    
    # Extract CSRF token
    csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', response.content.decode())
    if not csrf_match:
        print("❌ CSRF token not found")
        return False
    
    csrf_token = csrf_match.group(1)
    
    # Prepare login data
    login_data = {
        'login_submit': 'Log In',
        'login-username': 'testuser@example.com',
        'login-password': 'testpassword123',
        'login-redirect_url': '',
        'csrfmiddlewaretoken': csrf_token,
    }
    
    # Submit login form
    response = client.post('/en/accounts/login/', login_data, follow=True)
    
    # Check if redirected away from login page (successful login)
    final_url = response.request.get('PATH_INFO', '')
    if 'login' not in final_url:
        print("✅ Login successful")
        return True
    else:
        print("❌ Login failed")
        return False


def test_registration():
    """Test user registration functionality"""
    print("Testing registration functionality...")
    
    # Create a test client
    client = Client()
    
    # Get the login/registration page
    response = client.get('/en/accounts/login/')
    if response.status_code != 200:
        print("❌ Registration page not accessible")
        return False
    
    # Extract CSRF token
    csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', response.content.decode())
    if not csrf_match:
        print("❌ CSRF token not found")
        return False
    
    csrf_token = csrf_match.group(1)
    
    # Generate unique email for test
    import time
    test_email = f'testuser_{int(time.time())}@example.com'
    
    # Prepare registration data
    registration_data = {
        'registration_submit': 'Register',
        'registration-email': test_email,
        'registration-password1': 'testpassword123',
        'registration-password2': 'testpassword123',
        'registration-redirect_url': '',
        'csrfmiddlewaretoken': csrf_token,
    }
    
    # Submit registration form
    response = client.post('/en/accounts/login/', registration_data, follow=True)
    
    # Check if user was created
    try:
        new_user = User.objects.get(email=test_email)
        print(f"✅ Registration successful - User created: {new_user.username}")
        return True
    except User.DoesNotExist:
        print("❌ Registration failed - User not created")
        return False


def test_logout():
    """Test user logout functionality"""
    print("Testing logout functionality...")
    
    # Create a test client
    client = Client()
    
    # First login
    response = client.get('/en/accounts/login/')
    csrf_match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', response.content.decode())
    csrf_token = csrf_match.group(1) if csrf_match else 'dummy'
    
    login_data = {
        'login_submit': 'Log In',
        'login-username': 'testuser@example.com',
        'login-password': 'testpassword123',
        'login-redirect_url': '',
        'csrfmiddlewaretoken': csrf_token,
    }
    
    client.post('/en/accounts/login/', login_data, follow=True)
    
    # Now test logout
    response = client.get('/en/accounts/logout/', follow=True)
    
    # Try to access a protected page
    profile_response = client.get('/en/accounts/profile/')
    
    if profile_response.status_code == 302:
        print("✅ Logout successful - Redirected to login")
        return True
    else:
        print("❌ Logout failed - Still logged in")
        return False


def main():
    """Run all authentication tests"""
    print("🔐 Testing Django Oscar Authentication System")
    print("=" * 50)
    
    # Ensure test user exists
    try:
        User.objects.get(email='testuser@example.com')
    except User.DoesNotExist:
        User.objects.create_user('testuser@example.com', 'testuser@example.com', 'testpassword123')
        print("📝 Created test user: testuser@example.com")
    
    tests = [
        test_login,
        test_registration,
        test_logout,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            results.append(False)
        print()
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All authentication tests passed! Login and registration are working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the authentication configuration.")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
