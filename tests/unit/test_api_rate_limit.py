"""
Unit tests for rate limiting decorator in helpers.py

Tests cover:
- Basic rate limiting functionality
- Valid time periods (1, 60, 3600, 86400 seconds)
- Multiple IPs
- X-Forwarded-For header handling
- Rate limit headers
- 429 response format
- Sliding window behavior
- Input validation (count > 0, valid periods)
"""

import time
import unittest
from unittest.mock import Mock, patch

import flask

from pyload.webui.app.helpers import rate_limit


class TestRateLimitDecorator(unittest.TestCase):
    """Test suite for the rate_limit decorator."""

    def setUp(self):
        """Set up test Flask application."""
        self.app = flask.Flask(__name__)
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

        # Create test endpoints with different rate limits
        @self.app.route('/api/test-basic')
        @rate_limit(count=5, period=60)
        def test_basic():
            return flask.json.jsonify({"status": "ok"})

        @self.app.route('/api/test-per-second')
        @rate_limit(count=2, period=1)
        def test_per_second():
            return flask.json.jsonify({"status": "ok"})

        @self.app.route('/api/test-per-minute')
        @rate_limit(count=10, period=60)
        def test_per_minute():
            return flask.json.jsonify({"status": "ok"})

        @self.app.route('/api/test-per-hour')
        @rate_limit(count=100, period=3600)
        def test_per_hour():
            return flask.json.jsonify({"status": "ok"})

        @self.app.route('/api/test-per-day')
        @rate_limit(count=1000, period=86400)
        def test_per_day():
            return flask.json.jsonify({"status": "ok"})

        @self.app.route('/api/test-default')
        @rate_limit()  # Uses default: count=100, period=60
        def test_default():
            return flask.json.jsonify({"status": "ok"})

    def test_basic_rate_limit_allows_requests_within_limit(self):
        """Test that requests within the rate limit are allowed."""
        for i in range(5):
            response = self.client.get('/api/test-basic')
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(data['status'], 'ok')

    def test_basic_rate_limit_blocks_excess_requests(self):
        """Test that requests exceeding the rate limit are blocked."""
        # Make 5 allowed requests
        for i in range(5):
            response = self.client.get('/api/test-basic')
            self.assertEqual(response.status_code, 200)

        # 6th request should be blocked
        response = self.client.get('/api/test-basic')
        self.assertEqual(response.status_code, 429)
        data = response.get_json()
        self.assertEqual(data['error'], 'Rate limit exceeded')
        self.assertIn('retry_after', data)

    def test_rate_limit_headers_present(self):
        """Test that rate limit headers are included in responses."""
        response = self.client.get('/api/test-basic')

        self.assertIn('X-RateLimit-Limit', response.headers)
        self.assertIn('X-RateLimit-Remaining', response.headers)
        self.assertIn('X-RateLimit-Reset', response.headers)

        self.assertEqual(response.headers['X-RateLimit-Limit'], '5')
        self.assertEqual(response.headers['X-RateLimit-Remaining'], '4')

    def test_rate_limit_headers_on_429_response(self):
        """Test that 429 responses include proper headers."""
        # Exhaust the rate limit
        for i in range(5):
            self.client.get('/api/test-basic')

        # Get the 429 response
        response = self.client.get('/api/test-basic')

        self.assertEqual(response.status_code, 429)
        self.assertIn('Retry-After', response.headers)
        self.assertIn('X-RateLimit-Limit', response.headers)
        self.assertIn('X-RateLimit-Remaining', response.headers)
        self.assertIn('X-RateLimit-Reset', response.headers)

        self.assertEqual(response.headers['X-RateLimit-Remaining'], '0')

        # Retry-After should be a positive integer
        retry_after = int(response.headers['Retry-After'])
        self.assertGreater(retry_after, 0)
        self.assertLessEqual(retry_after, 60)

    def test_rate_limit_per_second(self):
        """Test rate limiting with period=1 (per second)."""
        # Should allow 2 requests
        for i in range(2):
            response = self.client.get('/api/test-per-second')
            self.assertEqual(response.status_code, 200)

        # 3rd request should be blocked
        response = self.client.get('/api/test-per-second')
        self.assertEqual(response.status_code, 429)

    def test_rate_limit_per_minute(self):
        """Test rate limiting with period=60 (per minute)."""
        # Should allow 10 requests
        for i in range(10):
            response = self.client.get('/api/test-per-minute')
            self.assertEqual(response.status_code, 200)

        # 11th request should be blocked
        response = self.client.get('/api/test-per-minute')
        self.assertEqual(response.status_code, 429)

    def test_rate_limit_per_hour(self):
        """Test rate limiting with period=3600 (per hour)."""
        # Should allow 100 requests
        for i in range(100):
            response = self.client.get('/api/test-per-hour')
            self.assertEqual(response.status_code, 200)

        # 101st request should be blocked
        response = self.client.get('/api/test-per-hour')
        self.assertEqual(response.status_code, 429)

    def test_rate_limit_per_day(self):
        """Test rate limiting with period=86400 (per day)."""
        # Should allow many requests
        for i in range(50):
            response = self.client.get('/api/test-per-day')
            self.assertEqual(response.status_code, 200)

        # Should still have remaining capacity
        remaining = int(response.headers['X-RateLimit-Remaining'])
        self.assertGreater(remaining, 900)

    def test_rate_limit_default_values(self):
        """Test that default values (count=100, period=60) work correctly."""
        # Should allow 100 requests
        for i in range(100):
            response = self.client.get('/api/test-default')
            self.assertEqual(response.status_code, 200)

        # 101st request should be blocked
        response = self.client.get('/api/test-default')
        self.assertEqual(response.status_code, 429)

    def test_rate_limit_different_ips(self):
        """Test that rate limits are tracked separately per IP."""
        # Make 5 requests from IP 1
        for i in range(5):
            response = self.client.get(
                '/api/test-basic',
                environ_base={'REMOTE_ADDR': '192.168.1.1'}
            )
            self.assertEqual(response.status_code, 200)

        # 6th request from IP 1 should be blocked
        response = self.client.get(
            '/api/test-basic',
            environ_base={'REMOTE_ADDR': '192.168.1.1'}
        )
        self.assertEqual(response.status_code, 429)

        # But requests from IP 2 should still work
        response = self.client.get(
            '/api/test-basic',
            environ_base={'REMOTE_ADDR': '192.168.1.2'}
        )
        self.assertEqual(response.status_code, 200)

    def test_rate_limit_x_forwarded_for_header(self):
        """Test that X-Forwarded-For header is used for IP detection."""
        # Make requests with X-Forwarded-For header
        for i in range(5):
            response = self.client.get(
                '/api/test-basic',
                headers={'X-Forwarded-For': '10.0.0.1, 192.168.1.1'}
            )
            self.assertEqual(response.status_code, 200)

        # 6th request should be blocked
        response = self.client.get(
            '/api/test-basic',
            headers={'X-Forwarded-For': '10.0.0.1, 192.168.1.1'}
        )
        self.assertEqual(response.status_code, 429)

        # Different X-Forwarded-For IP should work
        response = self.client.get(
            '/api/test-basic',
            headers={'X-Forwarded-For': '10.0.0.2'}
        )
        self.assertEqual(response.status_code, 200)

    def test_rate_limit_x_forwarded_for_takes_first_ip(self):
        """Test that only the first IP in X-Forwarded-For is used."""
        # Make requests with same first IP but different second IP
        for i in range(5):
            response = self.client.get(
                '/api/test-basic',
                headers={'X-Forwarded-For': f'10.0.0.1, 192.168.1.{i}'}
            )
            self.assertEqual(response.status_code, 200)

        # Should be blocked because first IP (10.0.0.1) is the same
        response = self.client.get(
            '/api/test-basic',
            headers={'X-Forwarded-For': '10.0.0.1, 192.168.1.99'}
        )
        self.assertEqual(response.status_code, 429)

    def test_rate_limit_response_format(self):
        """Test the format of the 429 response."""
        # Exhaust rate limit
        for i in range(5):
            self.client.get('/api/test-basic')

        # Get 429 response
        response = self.client.get('/api/test-basic')
        data = response.get_json()

        # Check response structure
        self.assertIn('error', data)
        self.assertIn('message', data)
        self.assertIn('retry_after', data)

        self.assertEqual(data['error'], 'Rate limit exceeded')
        self.assertIsInstance(data['retry_after'], int)
        self.assertGreater(data['retry_after'], 0)

        # Check message format
        self.assertIn('Too many requests', data['message'])

    def test_rate_limit_remaining_decrements(self):
        """Test that X-RateLimit-Remaining decrements correctly."""
        for i in range(5):
            response = self.client.get('/api/test-basic')
            remaining = int(response.headers['X-RateLimit-Remaining'])
            expected_remaining = 4 - i
            self.assertEqual(remaining, expected_remaining)

    def test_rate_limit_reset_timestamp(self):
        """Test that X-RateLimit-Reset timestamp is reasonable."""
        response = self.client.get('/api/test-basic')

        reset_timestamp = int(response.headers['X-RateLimit-Reset'])
        current_time = int(time.time())

        # Reset should be in the future but within the period (60 seconds)
        self.assertGreater(reset_timestamp, current_time)
        self.assertLessEqual(reset_timestamp, current_time + 60)

    def test_rate_limit_multiple_endpoints_independent(self):
        """Test that different endpoints have independent rate limits."""
        # Exhaust limit on one endpoint
        for i in range(5):
            response = self.client.get('/api/test-basic')
            self.assertEqual(response.status_code, 200)

        # Should be blocked on this endpoint
        response = self.client.get('/api/test-basic')
        self.assertEqual(response.status_code, 429)

        # But other endpoint should still work
        response = self.client.get('/api/test-per-minute')
        self.assertEqual(response.status_code, 200)

    def test_rate_limit_with_tuple_response(self):
        """Test rate limiting works with tuple responses (body, status_code)."""
        @self.app.route('/api/test-tuple')
        @rate_limit(count=2, period=60)
        def test_tuple():
            return {"status": "ok"}, 200

        # First request should work
        response = self.client.get('/api/test-tuple')
        self.assertEqual(response.status_code, 200)
        self.assertIn('X-RateLimit-Limit', response.headers)

        # Second request should work
        response = self.client.get('/api/test-tuple')
        self.assertEqual(response.status_code, 200)

        # Third should be blocked
        response = self.client.get('/api/test-tuple')
        self.assertEqual(response.status_code, 429)


class TestRateLimitValidation(unittest.TestCase):
    """Test input validation for rate_limit decorator."""

    def test_zero_count_raises_error(self):
        """Test that count=0 raises ValueError."""
        with self.assertRaises(ValueError) as context:
            @rate_limit(count=0, period=60)
            def dummy():
                pass

        self.assertIn('count', str(context.exception).lower())

    def test_negative_count_raises_error(self):
        """Test that negative count raises ValueError."""
        with self.assertRaises(ValueError) as context:
            @rate_limit(count=-1, period=60)
            def dummy():
                pass

        self.assertIn('count', str(context.exception).lower())

    def test_invalid_period_raises_error(self):
        """Test that invalid period values raise ValueError."""
        invalid_periods = [0, 2, 30, 59, 61, 100, 3599, 3601, 86399, 86401, -1, -60]

        for invalid_period in invalid_periods:
            with self.subTest(period=invalid_period):
                with self.assertRaises(ValueError) as context:
                    @rate_limit(count=10, period=invalid_period)
                    def dummy():
                        pass

                self.assertIn('period', str(context.exception).lower())

    def test_valid_periods_accepted(self):
        """Test that all valid period values are accepted."""
        valid_periods = [1, 60, 3600, 86400]

        app = flask.Flask(__name__)

        for period in valid_periods:
            with self.subTest(period=period):
                # Should not raise any exception
                @app.route(f'/test-{period}', endpoint=f"dummy_{period}")
                @rate_limit(count=10, period=period)
                def dummy():
                    return "ok"

        # If we get here without exceptions, all periods are valid
        self.assertTrue(True)

    def test_float_count_raises_error(self):
        """Test that float count raises ValueError or TypeError."""
        with self.assertRaises((ValueError, TypeError)):
            @rate_limit(count=10.5, period=60)
            def dummy():
                pass

    def test_string_count_raises_error(self):
        """Test that string count raises ValueError or TypeError."""
        with self.assertRaises((ValueError, TypeError)):
            @rate_limit(count="10", period=60)
            def dummy():
                pass

    def test_string_period_raises_error(self):
        """Test that string period raises TypeError."""
        with self.assertRaises(TypeError):
            @rate_limit(count=10, period="minute")
            def dummy():
                pass


class TestRateLimitIntegration(unittest.TestCase):
    """Integration tests with actual API endpoints."""

    def setUp(self):
        """Set up test Flask application with realistic API."""
        self.app = flask.Flask(__name__)
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

        @self.app.route('/api/v1/status')
        @rate_limit(count=100, period=60)
        def api_status():
            return flask.json.jsonify({"status": "running", "version": "1.0"})

        @self.app.route('/api/v1/download/<int:file_id>')
        @rate_limit(count=10, period=60)
        def api_download(file_id):
            return flask.json.jsonify({"file_id": file_id, "url": f"/files/{file_id}"})

        @self.app.route('/api/v1/search')
        @rate_limit(count=30, period=60)
        def api_search():
            query = flask.request.args.get('q', '')
            return flask.json.jsonify({"query": query, "results": []})

        @self.app.route('/api/v1/upload')
        @rate_limit(count=5, period=3600)  # 5 per hour
        def api_upload():
            return flask.json.jsonify({"status": "uploaded"})

        @self.app.route('/api/v1/health')
        @rate_limit(count=1000, period=86400)  # 1000 per day
        def api_health():
            return flask.json.jsonify({"health": "ok"})

    def test_realistic_api_usage(self):
        """Test realistic API usage patterns."""
        # Normal usage - should all succeed
        for i in range(10):
            response = self.client.get(f'/api/v1/download/{i}')
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(data['file_id'], i)

        # 11th request should be rate limited
        response = self.client.get('/api/v1/download/10')
        self.assertEqual(response.status_code, 429)

    def test_status_endpoint_higher_limit(self):
        """Test that status endpoint has higher limit."""
        # Should be able to make many more requests to status
        for i in range(50):
            response = self.client.get('/api/v1/status')
            self.assertEqual(response.status_code, 200)

        # Should still have remaining requests
        self.assertIn('X-RateLimit-Remaining', response.headers)
        remaining = int(response.headers['X-RateLimit-Remaining'])
        self.assertGreater(remaining, 0)

    def test_mixed_endpoint_usage(self):
        """Test using multiple endpoints doesn't interfere with each other."""
        # Use status endpoint
        for i in range(10):
            self.client.get('/api/v1/status')

        # Use search endpoint
        for i in range(10):
            self.client.get('/api/v1/search?q=test')

        # Use download endpoint - should have full limit available
        for i in range(10):
            response = self.client.get(f'/api/v1/download/{i}')
            self.assertEqual(response.status_code, 200)

        # 11th download should be blocked
        response = self.client.get('/api/v1/download/10')
        self.assertEqual(response.status_code, 429)

    def test_hourly_rate_limit(self):
        """Test endpoint with hourly rate limit."""
        # Should allow 5 uploads
        for i in range(5):
            response = self.client.get('/api/v1/upload')
            self.assertEqual(response.status_code, 200)

        # 6th should be blocked
        response = self.client.get('/api/v1/upload')
        self.assertEqual(response.status_code, 429)

        # Retry-After should be reasonable (up to 3600 seconds)
        retry_after = int(response.headers['Retry-After'])
        self.assertGreater(retry_after, 0)
        self.assertLessEqual(retry_after, 3600)

    def test_daily_rate_limit(self):
        """Test endpoint with daily rate limit."""
        # Should allow many requests
        for i in range(100):
            response = self.client.get('/api/v1/health')
            self.assertEqual(response.status_code, 200)

        # Should still have plenty of capacity
        remaining = int(response.headers['X-RateLimit-Remaining'])
        self.assertGreater(remaining, 800)


if __name__ == '__main__':
    unittest.main()
