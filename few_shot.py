import json
import pandas as pd


class FewShotPosts:
    def __init__(self, file_path="data/processed_posts.json"):
        self.df = None
        self.unique_tags = None
        self.load_posts(file_path)

    def load_posts(self, file_path):
        with open(file_path, encoding="utf-8") as f:
            posts = json.load(f)
            df = pd.json_normalize(posts)
            df["length"] = df["line_count"].apply(self.categorize_length)
            self.df = df

            all_tags = [tag for sublist in self.df["tags"].dropna() for tag in sublist]
            self.unique_tags = set(all_tags)

    def categorize_length(self, line_count):
        if line_count < 5:
            return "Short"
        elif 5 <= line_count <= 10:
            return "Medium"
        else:
            return "Long"

    def get_tags(self):
        return self.unique_tags

    def get_filtered_posts(self, length, language, tag):
        if self.df is None:
            return []

        # Step 1: Exact match on Length + Language + Tag
        df_filtered = self.df[
            (self.df["language"].str.lower() == language.lower()) &
            (self.df["length"].str.lower() == length.lower()) &
            (self.df["tags"].apply(
                lambda tags: any(tag.lower() == t.lower() for t in tags) if isinstance(tags, list) else False
            ))
        ]

        # Step 2: Fallback to Language + Tag if exact length match is empty
        if df_filtered.empty:
            df_filtered = self.df[
                (self.df["language"].str.lower() == language.lower()) &
                (self.df["tags"].apply(
                    lambda tags: any(tag.lower() == t.lower() for t in tags) if isinstance(tags, list) else False
                ))
            ]

        return df_filtered.to_dict(orient="records")


if __name__ == "__main__":
    fs = FewShotPosts()

    # Slice [:1] to get only the first matching post, or [:2] for two posts
    posts = fs.get_filtered_posts("Short", "English", "Job Search")[:1]

    print(f"Found {len(posts)} matching post:\n")
    for i, post in enumerate(posts, 1):
        print(f"--- Post {i} ({post.get('length')} | {post.get('language')}) ---")
        print(post.get("text"))