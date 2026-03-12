"""Summarization Agent - Combines Chat History + Search Results"""
import logging
from typing import Dict, Any, List
from langchain_core.messages import SystemMessage

logger = logging.getLogger(__name__)


class SummarizationAgent:
    def __init__(self, model):
        self.model = model

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Create intelligent summary from conversation + search context"""

        # Build rich context
        chat_context = "\n".join([m.content for m in state['messages'][-8:]])
        search_context = ""

        if state.get('search_results'):
            search_info = f"Query: {state['search_query']}\n" + "\n".join(state['search_results'])
            search_context = search_info

        prompt = SystemMessage(content=f"""
        Create comprehensive summary (MAX 200 words) combining:

        CONVERSATION (last 8 exchanges):
        {chat_context}

        SEARCH RESULTS (if available):
        {search_context}

        Summary Structure:
        **Topics:** [main discussion points]
        **Key Findings:** [facts from chat + search]
        **Conclusions:** [insights, next steps]
        **Open Questions:** [unresolved items]

        Be concise but comprehensive.
        """)

        response = await self.model.ainvoke([prompt])
        summary = response.content

        logger.info("📝 Summarization Agent: Summary generated")
        return {
            "summary": summary,
            "summary_history": state.get('summary_history', []) + [summary],
            "current_phase": "respond",
            "needs_review": False
        }
