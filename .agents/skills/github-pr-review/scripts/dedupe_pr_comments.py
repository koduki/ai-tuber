import subprocess
import json
import sys
import argparse

def get_all_comments(pr_number):
    cmd = [
        "gh", "api",
        f"repos/koduki/ai-tuber/pulls/{pr_number}/comments"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error fetching comments: {result.stderr}")
        return []
    return json.loads(result.stdout)

def dedupe(pr_number, user_login):
    comments = get_all_comments(pr_number)
    seen = {}
    to_delete = []

    for c in comments:
        if c.get('user', {}).get('login') != user_login:
            continue
        
        key = (c.get('in_reply_to_id'), c.get('body'))
        if key in seen:
            to_delete.append(c['id'])
        else:
            seen[key] = c['id']

    if not to_delete:
        print("No duplicates found.")
        return

    print(f"Deleting {len(to_delete)} duplicates...")
    for comment_id in to_delete:
        cmd = [
            "gh", "api",
            "--method", "DELETE",
            f"repos/koduki/ai-tuber/pulls/comments/{comment_id}"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"Deleted {comment_id}")
        else:
            print(f"Failed to delete {comment_id}: {res.stderr}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pr_number", type=int)
    parser.add_argument("--user", default="koduki")
    args = parser.parse_args()
    dedupe(args.pr_number, args.user)
