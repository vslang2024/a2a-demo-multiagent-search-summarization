"""Search Agent - Pure LLM Search Query Generation + Results Simulation"""
import logging
from typing import Dict, Any, List
from langchain_core.messages import SystemMessage

logger = logging.getLogger(__name__)


class SearchAgent:
    def __init__(self, model):
        self.model = model

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate search query + simulate results from conversation context"""
        context = "\n".join([m.content for m in state['messages'][-5:]])

        # Generate precise search query
        query_prompt = SystemMessage(content=f"""
        You are a Search Query Generator. Analyze conversation and create BEST search query.

        Context: {context}

        Rules:
        - 3-8 words maximum
        - Focus on facts, news, current events
        - Format EXACTLY: QUERY: [search terms]

        Examples:
        "latest AI news" → QUERY: latest AI news 2026
        "who won election" → QUERY: 2026 election results
        """)

        query_response = await self.model.ainvoke([query_prompt])
        search_query = query_response.content.split("QUERY:")[-1].strip()

        # Simulate realistic search results (pure LLM reasoning)
        results_prompt = SystemMessage(content=f"""
        Simulate TOP 3 Google search results for: "{search_query}"

        Return EXACT format for each:
        Title | https://example.com/1 | 50-word informative snippet

        Make snippets realistic and relevant to the query.
        """)

        results_response = await self.model.ainvoke([results_prompt])
        search_results = []
        for line in results_response.content.split("\n"):
            if "|" in line and len(line.split("|")) == 3:
                search_results.append(line.strip())
                if len(search_results) == 3:
                    break

        logger.info(f"🔍 Search Agent: '{search_query}' → {len(search_results)} results")
        return {
            "search_query": search_query,
            "search_results": search_results,
            "current_phase": "summarize",
            "needs_search": False
        }

    def should_activate(self, messages: List) -> bool:
        """Smart trigger for search activation"""
        if not messages:
            return False
        recent = " ".join([m.content.lower() for m in messages[-3:]]).lower()
        triggers = ['what is', 'who is', 'latest', 'current', 'news', 'price', '2026']
        return any(trigger in recent for trigger in triggers)
