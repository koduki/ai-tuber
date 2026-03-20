import subprocess
import json
import argparse
import sys

def reply_to_comments(repo, pr_number, replies_dict):
    for comment_id, body in replies_dict.items():
        cmd = [
            "gh", "api",
            f"repos/{repo}/pulls/{pr_number}/comments",
            "-f", f"body={body}",
            "-F", f"in_reply_to={comment_id}"
        ]
        print(f"Replying to {comment_id}...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Replied to {comment_id}")
        else:
            print(f"Failed to reply to {comment_id}: {result.stderr}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("repo") # e.g. "koduki/ai-tuber"
    parser.add_argument("pr_number", type=int)
    parser.add_argument("replies_json", help="JSON string mapping comment ID as key and reply body as value")
    args = parser.parse_args()

    try:
        replies_dict = json.loads(args.replies_json)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        sys.exit(1)

    reply_to_comments(args.repo, args.pr_number, replies_dict)
