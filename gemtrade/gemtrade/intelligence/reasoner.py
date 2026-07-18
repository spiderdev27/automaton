"""
Deep Reasoner

Uses LLM to perform deep reasoning about market intelligence:
1. Connect indirect dots (supply chain → end product)
2. Infer hidden information (unusual activity → insider knowledge?)
3. Consider second-order effects (Fed policy → dollar → gold)
4. Challenge assumptions (is this really bullish?)
5. Generate trading thesis with full reasoning chain

This is the "thinking" brain of the intelligence system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any
from enum import Enum


class ReasoningType(Enum):
    """Type of reasoning being performed."""
    DIRECT = "direct"               # A directly causes B
    INDIRECT = "indirect"           # A → B → C
    CONTRARIAN = "contrarian"       # Crowd is wrong because...
    HIDDEN = "hidden"               # Reading between the lines
    SECOND_ORDER = "second_order"   # Consequence of consequence
    SYNTHESIS = "synthesis"         # Multiple factors combined


@dataclass
class Inference:
    """
    A single inference/conclusion from reasoning.
    """
    statement: str
    confidence: float       # 0-1
    reasoning_type: ReasoningType
    supporting_evidence: List[str]
    counter_evidence: List[str]
    
    def net_confidence(self) -> float:
        """Adjust confidence by counter-evidence."""
        counter_penalty = len(self.counter_evidence) * 0.1
        return max(0, self.confidence - counter_penalty)


@dataclass
class ReasoningChain:
    """
    A chain of reasoning leading to a conclusion.
    
    Shows the full thought process.
    """
    id: str
    timestamp: datetime
    
    # Question being answered
    question: str
    
    # The reasoning steps
    steps: List[Inference] = field(default_factory=list)
    
    # Final conclusion
    conclusion: str = ""
    conclusion_confidence: float = 0.0
    
    # Trading implication
    trading_action: str = "none"
    action_urgency: str = "low"
    
    # Full reasoning text (for transparency)
    full_reasoning: str = ""
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "question": self.question,
            "steps": [
                {
                    "statement": s.statement,
                    "confidence": s.confidence,
                    "type": s.reasoning_type.value,
                }
                for s in self.steps
            ],
            "conclusion": self.conclusion,
            "confidence": self.conclusion_confidence,
            "trading_action": self.trading_action,
            "full_reasoning": self.full_reasoning,
        }


class DeepReasoner:
    """
    LLM-powered deep reasoning about market intelligence.
    
    Capabilities:
    1. Multi-hop reasoning (A → B → C → D)
    2. Indirect effect detection
    3. Hidden signal inference
    4. Contrarian analysis
    5. Thesis generation with full transparency
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.reasoning_history: List[ReasoningChain] = []
        
        # Knowledge base for reasoning
        self.knowledge_base = self._init_knowledge_base()
    
    def _init_knowledge_base(self) -> Dict[str, Any]:
        """
        Initialize knowledge base for reasoning.
        
        This contains relationships the LLM should know about.
        """
        return {
            # Asset relationships
            "correlations": {
                "XAUUSD": {
                    "positive": ["SILVER", "GDX", "inflation_expectations"],
                    "negative": ["DXY", "real_yields", "risk_on"],
                },
                "BTCUSD": {
                    "positive": ["ETHUSD", "risk_on", "liquidity"],
                    "negative": ["DXY", "regulation_fears"],
                },
            },
            
            # Causal chains
            "causal_chains": [
                {
                    "trigger": "fed_rate_hike",
                    "chain": [
                        "higher interest rates",
                        "stronger dollar (DXY up)",
                        "gold priced in USD becomes more expensive",
                        "gold demand decreases",
                        "XAUUSD falls"
                    ],
                    "typical_lag": "immediate to 1 hour",
                },
                {
                    "trigger": "inflation_higher_than_expected",
                    "chain": [
                        "real value of cash decreases",
                        "gold as inflation hedge more attractive",
                        "BUT Fed may hike rates more",
                        "initial gold rally, then depends on Fed reaction"
                    ],
                    "typical_lag": "immediate rally, Fed reaction in days",
                },
                {
                    "trigger": "geopolitical_crisis",
                    "chain": [
                        "uncertainty increases",
                        "flight to safety",
                        "gold is traditional safe haven",
                        "XAUUSD rallies"
                    ],
                    "typical_lag": "immediate",
                },
                {
                    "trigger": "major_exchange_hack",
                    "chain": [
                        "trust in centralized exchanges decreases",
                        "users withdraw to cold storage",
                        "short-term panic selling",
                        "BUT long-term: proves need for decentralization"
                    ],
                    "typical_lag": "immediate crash, recovery in days",
                },
            ],
            
            # Hidden signal indicators
            "hidden_signals": {
                "unusual_options_volume": "Potential insider knowledge",
                "dark_pool_activity": "Institutional positioning",
                "insider_selling_cluster": "Executives know something bad",
                "insider_buying_cluster": "Executives know something good",
                "exchange_outflow_spike": "Whales accumulating (bullish)",
                "exchange_inflow_spike": "Whales preparing to sell (bearish)",
            },
            
            # Indirect relationships
            "indirect_effects": {
                "chip_shortage": ["tech stocks", "auto stocks", "crypto mining"],
                "oil_price_spike": ["airlines", "shipping", "inflation", "gold"],
                "china_lockdown": ["supply chains", "commodities", "global growth"],
                "bank_failure": ["financial contagion", "flight to safety", "gold"],
            },
        }
    
    async def reason_about(
        self,
        question: str,
        context: Dict[str, Any],
        depth: int = 3
    ) -> ReasoningChain:
        """
        Perform deep reasoning about a question.
        
        Args:
            question: The question to reason about
            context: Relevant market context
            depth: How many levels deep to reason
            
        Returns:
            ReasoningChain with full thought process
        """
        chain = ReasoningChain(
            id=f"reason_{datetime.utcnow().timestamp()}",
            timestamp=datetime.utcnow(),
            question=question,
        )
        
        # This would call the LLM with structured prompts
        # For now, showing the structure
        
        prompt = self._build_reasoning_prompt(question, context, depth)
        
        # LLM would return structured reasoning
        # We parse it into steps
        
        chain.full_reasoning = f"[LLM reasoning would go here for: {question}]"
        
        self.reasoning_history.append(chain)
        return chain
    
    def _build_reasoning_prompt(
        self,
        question: str,
        context: Dict,
        depth: int
    ) -> str:
        """Build prompt for LLM reasoning."""
        return f"""
You are a senior market analyst with 20 years of experience.

QUESTION: {question}

CONTEXT:
{self._format_context(context)}

KNOWLEDGE BASE:
{self._format_knowledge_base()}

INSTRUCTIONS:
1. Think step by step
2. Consider direct AND indirect effects
3. Look for hidden signals (unusual activity, timing, etc.)
4. Consider what the crowd might be missing
5. Trace causal chains up to {depth} levels deep
6. Challenge your own assumptions
7. Provide confidence level for each inference

FORMAT YOUR RESPONSE AS:

STEP 1: [First inference]
- Evidence: [supporting facts]
- Counter-evidence: [opposing facts]
- Confidence: [0-100%]

STEP 2: [Second inference]
...

CONCLUSION:
- Statement: [final conclusion]
- Confidence: [0-100%]
- Trading Action: [buy/sell/hold/none]
- Urgency: [immediate/high/medium/low]

FULL REASONING:
[Narrative explanation of your thinking]
"""
    
    def _format_context(self, context: Dict) -> str:
        """Format context for prompt."""
        lines = []
        for key, value in context.items():
            lines.append(f"- {key}: {value}")
        return "\n".join(lines)
    
    def _format_knowledge_base(self) -> str:
        """Format relevant knowledge for prompt."""
        # Would select relevant parts based on context
        return str(self.knowledge_base)
    
    async def detect_indirect_effects(
        self,
        event: str,
        target_symbol: str
    ) -> List[Inference]:
        """
        Detect indirect effects of an event on a symbol.
        
        Example: "Chip shortage" → effect on BTCUSD?
        Chain: Chip shortage → GPU prices up → mining costs up → 
               hashrate might decrease → network security concern →
               BUT also → fewer new miners → supply restriction → 
               could be neutral to slightly bearish short-term
        """
        inferences = []
        
        # Check knowledge base for known indirect effects
        for trigger, affected in self.knowledge_base["indirect_effects"].items():
            if trigger.lower() in event.lower():
                if any(a.lower() in target_symbol.lower() for a in affected):
                    inferences.append(Inference(
                        statement=f"'{trigger}' has known indirect effect on {target_symbol}",
                        confidence=0.7,
                        reasoning_type=ReasoningType.INDIRECT,
                        supporting_evidence=[f"Historical pattern: {trigger} affects {affected}"],
                        counter_evidence=[],
                    ))
        
        # LLM would discover new indirect effects not in knowledge base
        
        return inferences
    
    async def detect_hidden_signals(
        self,
        market_data: Dict[str, Any]
    ) -> List[Inference]:
        """
        Detect potential hidden signals in market data.
        
        Looking for:
        - Unusual options activity
        - Dark pool movements
        - Insider trading patterns
        - Exchange flow anomalies
        - Unusual correlations breaking
        """
        inferences = []
        
        # Check for known hidden signal patterns
        for signal_type, meaning in self.knowledge_base["hidden_signals"].items():
            # Would check actual data here
            pass
        
        return inferences
    
    async def generate_trading_thesis(
        self,
        symbol: str,
        intelligence: List[Dict],
        current_position: Optional[Dict] = None
    ) -> ReasoningChain:
        """
        Generate a complete trading thesis with full reasoning.
        
        This is the culmination of all intelligence:
        1. Synthesize all available information
        2. Reason about direct and indirect effects
        3. Consider contrarian view
        4. Generate actionable thesis
        """
        question = f"Should I be long, short, or flat on {symbol} right now?"
        
        context = {
            "symbol": symbol,
            "intelligence_count": len(intelligence),
            "current_position": current_position,
        }
        
        chain = await self.reason_about(question, context, depth=4)
        
        return chain
    
    async def challenge_thesis(
        self,
        thesis: str,
        symbol: str
    ) -> ReasoningChain:
        """
        Challenge an existing thesis - find holes.
        
        This is adversarial reasoning:
        "Why might this thesis be WRONG?"
        """
        question = f"Why might the thesis '{thesis}' be wrong for {symbol}?"
        
        chain = await self.reason_about(
            question,
            {"thesis": thesis, "symbol": symbol},
            depth=3
        )
        
        return chain


# Example prompts for different reasoning tasks
REASONING_PROMPTS = {
    "indirect_effect": """
Given this event: {event}
How might it affect {symbol}?

Think through the chain of effects:
1. What is the immediate impact?
2. What are the second-order effects?
3. What are the third-order effects?
4. How long before each effect materializes?

Be specific about the causal chain.
""",

    "hidden_signal": """
Analyze this market data for hidden signals:
{data}

Look for:
- Unusual volume patterns
- Divergences from normal behavior
- Potential insider activity
- Smart money positioning

What might this data be telling us that isn't obvious?
""",

    "contrarian": """
The current market consensus on {symbol} is: {consensus}

Reasons given: {reasons}

Now argue the OPPOSITE case:
1. What is the crowd missing?
2. What assumptions might be wrong?
3. What would make the consensus wrong?
4. Historical examples where similar consensus was wrong?

Be specific and evidence-based.
""",

    "synthesis": """
Here is intelligence from multiple sources about {symbol}:

{intelligence}

Synthesize this into a coherent view:
1. What do the sources agree on?
2. Where do they disagree?
3. What is the most likely outcome?
4. What would change this view?

Provide a clear, actionable conclusion.
""",
}
