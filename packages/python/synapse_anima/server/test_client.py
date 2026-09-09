"""
Test client for Synapse Anima FastAPI Server.

This script demonstrates how to interact with the server API endpoints
and WebSocket interface. Useful for testing and integration examples.
"""

import asyncio
import json
import requests
import websockets


# ===== Configuration =====

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws/chat"
USER_ID = "test_user_123"
SESSION_ID = "test_session"


# ===== REST API Examples =====

def test_health_check():
    """Test health check endpoint."""
    print("\n=== Testing Health Check ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()


def test_chat_endpoint():
    """Test chat endpoint (non-streaming)."""
    print("\n=== Testing Chat Endpoint ===")

    payload = {
        "message": "Hello! I'm feeling excited about learning new things.",
        "user_id": USER_ID,
        "session_id": SESSION_ID,
        "personality_mode": "balanced",
        "reasoning_mode": "quick"
    }

    response = requests.post(f"{BASE_URL}/api/v1/chat", json=payload)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Content: {data['content']}")
        print(f"Emotions: {json.dumps(data.get('emotions', {}), indent=2)}")
        print(f"Wonder Index: {data.get('wonder_index')}")
    else:
        print(f"Error: {response.text}")

    return response.json() if response.status_code == 200 else None


def test_beliefs_api():
    """Test beliefs API endpoints."""
    print("\n=== Testing Beliefs API ===")

    # Create belief
    print("\n1. Creating belief...")
    belief_data = {
        "statement": "I believe in continuous learning and growth",
        "category": "values",
        "strength": 0.9,
        "user_confirmed": True
    }

    response = requests.post(
        f"{BASE_URL}/api/v1/beliefs",
        params={"user_id": USER_ID},
        json=belief_data
    )
    print(f"Create Status: {response.status_code}")

    if response.status_code == 201:
        belief = response.json()
        belief_id = belief["belief_id"]
        print(f"Created Belief ID: {belief_id}")

        # Get beliefs
        print("\n2. Getting beliefs...")
        response = requests.get(
            f"{BASE_URL}/api/v1/beliefs",
            params={"user_id": USER_ID}
        )
        print(f"Get Status: {response.status_code}")
        print(f"Beliefs Count: {len(response.json())}")

        # Get statistics
        print("\n3. Getting statistics...")
        response = requests.get(
            f"{BASE_URL}/api/v1/beliefs/statistics",
            params={"user_id": USER_ID}
        )
        print(f"Statistics: {json.dumps(response.json(), indent=2)}")

        return belief_id
    else:
        print(f"Error: {response.text}")
        return None


def test_goals_api():
    """Test goals API endpoints."""
    print("\n=== Testing Goals API ===")

    # Create goal
    print("\n1. Creating goal...")
    goal_data = {
        "title": "Learn Python FastAPI",
        "description": "Master FastAPI framework for building APIs",
        "category": "learning",
        "priority": 4,
        "wonder_index": 0.7,
        "emotional_intensity": 0.8
    }

    response = requests.post(
        f"{BASE_URL}/api/v1/goals",
        params={"user_id": USER_ID},
        json=goal_data
    )
    print(f"Create Status: {response.status_code}")

    if response.status_code == 201:
        goal = response.json()
        goal_id = goal["goal_id"]
        print(f"Created Goal ID: {goal_id}")

        # Update progress
        print("\n2. Updating progress...")
        response = requests.patch(
            f"{BASE_URL}/api/v1/goals/{goal_id}/progress",
            params={"user_id": USER_ID},
            json={"progress": 0.5, "status": "in_progress"}
        )
        print(f"Update Status: {response.status_code}")

        # Get goals
        print("\n3. Getting goals...")
        response = requests.get(
            f"{BASE_URL}/api/v1/goals",
            params={"user_id": USER_ID}
        )
        print(f"Goals Count: {len(response.json())}")

        # Get statistics
        print("\n4. Getting statistics...")
        response = requests.get(
            f"{BASE_URL}/api/v1/goals/statistics",
            params={"user_id": USER_ID}
        )
        print(f"Statistics: {json.dumps(response.json(), indent=2)}")

        return goal_id
    else:
        print(f"Error: {response.text}")
        return None


def test_memory_api():
    """Test memory API endpoints."""
    print("\n=== Testing Memory API ===")

    # Create memory
    print("\n1. Creating memory...")
    memory_data = {
        "content": "Had an amazing breakthrough about async programming today!",
        "memory_type": "breakthrough",
        "scope": "core",
        "wonder_index": 0.9,
        "metadata": {"tags": ["programming", "learning"]}
    }

    response = requests.post(
        f"{BASE_URL}/api/v1/memories",
        params={"user_id": USER_ID},
        json=memory_data
    )
    print(f"Create Status: {response.status_code}")

    if response.status_code == 201:
        memory = response.json()
        memory_id = memory["memory_id"]
        print(f"Created Memory ID: {memory_id}")

        # Search memories
        print("\n2. Searching memories...")
        response = requests.get(
            f"{BASE_URL}/api/v1/memories/search",
            params={
                "user_id": USER_ID,
                "query": "programming",
                "limit": 10
            }
        )
        print(f"Search Results: {len(response.json())}")

        # Get breakthroughs
        print("\n3. Getting breakthroughs...")
        response = requests.get(
            f"{BASE_URL}/api/v1/memories/breakthroughs",
            params={"user_id": USER_ID, "min_significance": 0.7}
        )
        print(f"Breakthroughs: {len(response.json())}")

        return memory_id
    else:
        print(f"Error: {response.text}")
        return None


def test_preferences_api():
    """Test preferences API endpoints."""
    print("\n=== Testing Preferences API ===")

    # Get current preferences
    print("\n1. Getting current preferences...")
    response = requests.get(
        f"{BASE_URL}/api/v1/preferences",
        params={"user_id": USER_ID}
    )
    print(f"Get Status: {response.status_code}")
    print(f"Preferences: {json.dumps(response.json(), indent=2)}")

    # Update preferences
    print("\n2. Updating preferences...")
    updates = {
        "communication_style": "casual",
        "response_verbosity": "detailed",
        "emoji_usage": "moderate"
    }

    response = requests.patch(
        f"{BASE_URL}/api/v1/preferences",
        params={"user_id": USER_ID},
        json=updates
    )
    print(f"Update Status: {response.status_code}")
    print(f"Updated: {json.dumps(response.json(), indent=2)}")

    # Get schema
    print("\n3. Getting preferences schema...")
    response = requests.get(f"{BASE_URL}/api/v1/preferences/schema")
    print(f"Schema keys: {list(response.json().keys())}")


# ===== WebSocket Examples =====

async def test_websocket_chat():
    """Test WebSocket streaming chat."""
    print("\n=== Testing WebSocket Chat ===")

    uri = f"{WS_URL}?user_id={USER_ID}&session_id={SESSION_ID}"

    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket")

            # Receive welcome message
            message = await websocket.recv()
            data = json.loads(message)
            print(f"Received: {data['type']} - {data.get('event', 'N/A')}")

            # Send chat message
            print("\nSending chat message...")
            chat_message = {
                "type": "chat",
                "content": "Tell me about the importance of emotional intelligence!",
                "reasoning_mode": "quick"
            }
            await websocket.send(json.dumps(chat_message))

            # Receive responses
            response_chunks = []
            while True:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    data = json.loads(message)

                    msg_type = data.get("type")
                    print(f"Received: {msg_type}")

                    if msg_type == "status":
                        print(f"  Status: {data.get('message')}")

                    elif msg_type == "emotion":
                        print(f"  Emotion: {json.dumps(data.get('data'), indent=2)}")

                    elif msg_type == "chunk":
                        chunk = data.get("content", "")
                        response_chunks.append(chunk)
                        print(f"  Chunk: {chunk[:50]}...")

                    elif msg_type == "complete":
                        print(f"  Complete! Metadata: {data.get('metadata')}")
                        break

                    elif msg_type == "error":
                        print(f"  Error: {data.get('error')}")
                        break

                except asyncio.TimeoutError:
                    print("Timeout waiting for response")
                    break

            # Print full response
            full_response = "".join(response_chunks)
            print(f"\nFull Response:\n{full_response}")

            # Send ping
            print("\nSending ping...")
            await websocket.send(json.dumps({"type": "ping"}))
            pong = await websocket.recv()
            print(f"Received: {json.loads(pong)['type']}")

    except Exception as e:
        print(f"WebSocket error: {e}")


# ===== Main Test Runner =====

def run_all_tests():
    """Run all API tests."""
    print("=" * 60)
    print("Synapse Anima FastAPI Server - Test Suite")
    print("=" * 60)

    # REST API tests
    test_health_check()
    test_chat_endpoint()
    test_beliefs_api()
    test_goals_api()
    test_memory_api()
    test_preferences_api()

    # WebSocket test
    print("\n" + "=" * 60)
    asyncio.run(test_websocket_chat())

    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    print("\nMake sure the server is running on http://localhost:8000")
    print("Start server with: python -m synapse_anima.server.example\n")

    input("Press Enter to start tests...")

    run_all_tests()
