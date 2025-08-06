import os
from atlassian import Confluence
from dotenv import load_dotenv

load_dotenv()


class ConfluenceAPI:
    """
    A class to wrap Confluence API calls for creating and listing pages.
    """
    def __init__(self):
        self.confluence_url = os.getenv("CONFLUENCE_URL")
        self.username = os.getenv("CONFLUENCE_USERNAME")
        self.api_token = os.getenv("CONFLUENCE_API_TOKEN")

        if not all([self.confluence_url, self.username, self.api_token]):
            raise ValueError("Confluence credentials not found in environment variables.")

        self.confluence = Confluence(
            url=self.confluence_url,
            username=self.username,
            password=self.api_token
        )

    def create_page(self, space_key: str, title: str, body: str) -> str:
        """
        Creates a new page in a given Confluence space.

        Args:
            space_key (str): The key of the space to create the page in.
            title (str): The title of the new page.
            body (str): The content of the page (in storage format).

        Returns:
            str: A message indicating success or failure.
        """
        try:
            # Check if page already exists to avoid duplicates
            page = self.confluence.get_page_by_title(space=space_key, title=title)
            if page:
                return f"Page with title '{title}' already exists in space '{space_key}'. No new page was created."

            # Create the new page
            response = self.confluence.create_page(
                space=space_key,
                title=title,
                body=body,
                parent_id=None,
                type='page',
                representation='storage'
            )
            page_id = response.get('id')
            page_url = f"{self.confluence_url}/pages/viewpage.action?pageId={page_id}"
            return f"Successfully created page '{title}' in space '{space_key}'. URL: {page_url}"

        except Exception as e:
            return f"An error occurred while creating the page: {e}"

    def list_pages(self, space_key: str, query: str = None) -> str:
        """
        Lists pages in a Confluence space, optionally filtered by a query.

        Args:
            space_key (str): The key of the Confluence space.
            query (str, optional): A search query to filter pages. Defaults to None.

        Returns:
            str: A formatted string of page titles or a message if no pages are found.
        """
        try:
            if query:
                cql_query = f'space = "{space_key}" AND title ~ "{query}"'
                results = self.confluence.cql(cql=cql_query, limit=10).get('results')
            else:
                results = self.confluence.get_all_pages_from_space(space=space_key, limit=10)

            if not results:
                return f"No pages found in space '{space_key}' that match the criteria."

            page_titles = [page.get('title') for page in results]
            formatted_list = "\n".join(f"- {title}" for title in page_titles)
            return f"Here are the pages found in space '{space_key}':\n{formatted_list}"

        except Exception as e:
            return f"An error occurred while listing pages: {e}"
