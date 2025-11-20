"""LLM service with intelligent model routing."""

import os
import re
from typing import Any, Dict, List, Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from utils.logging_config import get_logger

logger = get_logger(__name__)


class LLMService:
    """Service for managing LLM interactions with intelligent model routing."""

    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Initialize LLM service.

        Args:
            openai_api_key: OpenAI API key (if not provided, reads from env)
        """
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY must be provided or set in environment")

        # Initialize both models
        self.gpt4o_mini = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=self.api_key,
            temperature=0.7,
        )

        self.gpt4o = ChatOpenAI(
            model="gpt-4o",
            api_key=self.api_key,
            temperature=0.8,
        )

        logger.info("LLM service initialized with GPT-4o and GPT-4o-mini")

    def split_into_parts(self, text: str, max_words: int = 50) -> List[str]:
        """
        Split text into parts respecting complete sentences.

        Divides text into parts with max_words per part, ensuring complete sentences
        are kept together.

        Args:
            text: Text to split
            max_words: Maximum words per part (default: 50)

        Returns:
            List of text parts
        """
        # Split into sentences using regex (handles . ! ? followed by space or end)
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())

        parts = []
        current_part = []
        current_word_count = 0

        for sentence in sentences:
            # Count words in this sentence
            sentence_words = len(sentence.split())

            # If adding this sentence exceeds max_words, save current part and start new one
            if current_word_count + sentence_words > max_words and current_part:
                parts.append(' '.join(current_part))
                current_part = [sentence]
                current_word_count = sentence_words
            else:
                current_part.append(sentence)
                current_word_count += sentence_words

        # Add remaining part
        if current_part:
            parts.append(' '.join(current_part))

        logger.debug(f"Text split into {len(parts)} parts (max {max_words} words per part)")
        return parts

    def get_llm_for_task(self, task_type: str) -> ChatOpenAI:
        """
        Router to select appropriate LLM based on task type.

        Strategy:
        - extraction, classification, analysis → GPT-4o-mini (faster, cheaper)
        - response, closing, welcome → GPT-4o (better quality)

        Args:
            task_type: Type of task (extraction/classification/analysis/response/closing/welcome)

        Returns:
            Appropriate ChatOpenAI instance
        """
        lightweight_tasks = ["extraction", "classification", "analysis", "sentiment", "intent"]
        heavyweight_tasks = ["response", "closing", "welcome", "conversation"]

        if task_type.lower() in lightweight_tasks:
            logger.debug(f"Using GPT-4o-mini for task: {task_type}")
            return self.gpt4o_mini
        elif task_type.lower() in heavyweight_tasks:
            logger.debug(f"Using GPT-4o for task: {task_type}")
            return self.gpt4o
        else:
            # Default to GPT-4o-mini for unknown tasks
            logger.warning(f"Unknown task type '{task_type}', defaulting to GPT-4o-mini")
            return self.gpt4o_mini

    async def classify_intent(self, message: str, conversation_history: Optional[List[BaseMessage]] = None) -> Dict[str, Any]:
        """
        Classify user intent and calculate intent score.

        Args:
            message: User's message
            conversation_history: Previous messages for context

        Returns:
            Dict with intent category and score (0-1)
        """
        llm = self.get_llm_for_task("classification")

        prompt = f"""Analiza el siguiente mensaje de un cliente potencial y clasifica su intención.

Mensaje: "{message}"

Clasifica en una de estas categorías:
- browsing: Solo está mirando, no listo para comprar (puntuación: 0.0-0.3)
- interested: Muestra interés, hace preguntas (puntuación: 0.3-0.6)
- ready_to_buy: Señales claras de compra (puntuación: 0.6-0.9)
- objection: Tiene dudas u objeciones (puntuación: 0.4-0.6)
- leaving: Quiere terminar la conversación (puntuación: 0.0-0.2)

IMPORTANTE: Un saludo inicial como "hola", "buenos días", "hey" debe clasificarse como "interested" con puntuación entre 0.4-0.5, ya que el cliente está iniciando una conversación.

Responde SOLO con JSON válido en este formato exacto:
{{"category": "nombre_categoria", "score": 0.0}}"""

        try:
            messages = [HumanMessage(content=prompt)]
            response = await llm.ainvoke(messages)

            # Parse response
            import json
            result = json.loads(response.content)
            logger.info(f"Intent classified: {result}")
            return result
        except Exception as e:
            logger.error(f"Intent classification error: {e}")
            return {"category": "browsing", "score": 0.3}

    async def analyze_sentiment(self, message: str) -> str:
        """
        Analyze sentiment of user's message.

        Args:
            message: User's message

        Returns:
            Sentiment: positive/neutral/negative
        """
        llm = self.get_llm_for_task("sentiment")

        prompt = f"""Analiza el sentimiento de este mensaje del cliente.

Mensaje: "{message}"

Responde con UNA SOLA PALABRA: positive, neutral, o negative"""

        try:
            messages = [HumanMessage(content=prompt)]
            response = await llm.ainvoke(messages)
            sentiment = response.content.strip().lower()

            if sentiment not in ["positive", "neutral", "negative"]:
                sentiment = "neutral"

            logger.info(f"Sentiment analyzed: {sentiment}")
            return sentiment
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return "neutral"

    async def extract_data(self, message: str, conversation_history: Optional[List[BaseMessage]] = None) -> Dict[str, Any]:
        """
        Extract user data from message (name, email, needs, budget, etc.).

        Args:
            message: User's message
            conversation_history: Previous messages for context

        Returns:
            Dict with extracted data
        """
        llm = self.get_llm_for_task("extraction")

        prompt = f"""Extrae cualquier información del cliente de este mensaje.

Mensaje: "{message}"

Busca:
- name: Nombre del cliente
- email: Dirección de correo electrónico
- phone: Número de teléfono
- needs: Lo que está buscando
- budget: Presupuesto o rango de precios mencionado
- pain_points: Problemas que quiere resolver

Responde SOLO con JSON válido. Si un campo no está presente, usa null.
{{"name": null, "email": null, "phone": null, "needs": null, "budget": null, "pain_points": null}}"""

        try:
            messages = [HumanMessage(content=prompt)]
            response = await llm.ainvoke(messages)

            import json
            result = json.loads(response.content)
            # Filter out null values
            result = {k: v for k, v in result.items() if v is not None}
            logger.info(f"Data extracted: {result}")
            return result
        except Exception as e:
            logger.error(f"Data extraction error: {e}")
            return {}

    async def generate_response(
        self,
        messages: List[BaseMessage],
        system_prompt: str,
        use_emojis: bool = True,
        rag_context: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate conversational response.

        Args:
            messages: Conversation history
            system_prompt: System prompt with instructions
            use_emojis: Whether to include emojis
            rag_context: Optional RAG context to include
            config: Configuration dict with multi_part_messages and max_words_per_response

        Returns:
            Generated response text (may include [PAUSA] separators if multi_part_messages is enabled)
        """
        llm = self.get_llm_for_task("response")

        # Extract config values with defaults
        config = config or {}
        multi_part_messages = config.get("multi_part_messages", False)
        max_words_per_response = config.get("max_words_per_response", 150)

        # Build enhanced system prompt
        enhanced_prompt = system_prompt

        # Add word limit instruction
        enhanced_prompt += f"\n\nIMPORTANTE: Limita tu respuesta a máximo {max_words_per_response} palabras."

        # Add emoji instruction
        if use_emojis:
            enhanced_prompt += "\n\nIMPORTANTE: Usa emojis de manera natural en tus respuestas para hacerlas más amigables y expresivas."
        else:
            enhanced_prompt += "\n\nIMPORTANTE: NO uses emojis en tus respuestas."

        if rag_context:
            enhanced_prompt += f"\n\nRELEVANT CONTEXT:\n{rag_context}\n\nUse this context to inform your response when relevant."

        # Prepare messages - convert BaseMessage objects to proper format
        full_messages = [SystemMessage(content=enhanced_prompt)]

        # Ensure all messages are properly formatted BaseMessage objects
        for msg in messages:
            if isinstance(msg, BaseMessage):
                full_messages.append(msg)
            elif isinstance(msg, dict):
                # If message is a dict, convert to proper BaseMessage
                if msg.get("role") == "user" or msg.get("role") == "human":
                    full_messages.append(HumanMessage(content=msg.get("content", "")))
                elif msg.get("role") == "assistant" or msg.get("role") == "ai":
                    from langchain_core.messages import AIMessage
                    full_messages.append(AIMessage(content=msg.get("content", "")))
                elif msg.get("role") == "system":
                    full_messages.append(SystemMessage(content=msg.get("content", "")))

        try:
            response = await llm.ainvoke(full_messages)
            response_text = response.content
            logger.info(f"Response generated (length: {len(response_text)})")

            # Apply multi-part message splitting if enabled
            if multi_part_messages:
                word_count = len(response_text.split())
                # Split if >= 20 words
                if word_count >= 20:
                    # Calculate words per part for 3 parts
                    words_per_part = word_count // 3 if word_count >= 30 else word_count // 2
                    parts = self.split_into_parts(response_text, max_words=words_per_part)

                    # Limit to 3 parts maximum
                    if len(parts) > 3:
                        # Merge extra parts into the last 3
                        parts = [parts[0], ' '.join(parts[1:-1]), parts[-1]]

                    if len(parts) > 1:
                        response_text = "\n\n[PAUSA]\n\n".join(parts)
                        logger.info(f"Response split into {len(parts)} parts for multi-part delivery")

            return response_text
        except Exception as e:
            logger.error(f"Response generation error: {e}", exc_info=True)
            return "I apologize, I'm having trouble responding right now. Could you please try again?"

    async def generate_closing_message(self, user_data: Dict[str, Any], payment_link: str) -> str:
        """
        Generate a closing message with payment link.

        Args:
            user_data: Collected user data
            payment_link: Payment link to include

        Returns:
            Closing message with payment link
        """
        llm = self.get_llm_for_task("closing")

        name = user_data.get("name", "")

        prompt = f"""Genera un mensaje de cierre cálido y profesional para un cliente que está listo para comprar.

Nombre del cliente: {name if name else "cliente"}
Link de pago: {payment_link}

El mensaje debe:
1. Agradecerles por su interés
2. Confirmar que están listos para proceder
3. Incluir el link de pago de forma natural
4. Animarlos a contactar si tienen preguntas
5. Ser conciso (máximo 2-3 oraciones)

Genera SOLO el texto del mensaje, sin comentarios adicionales."""

        try:
            messages = [HumanMessage(content=prompt)]
            response = await llm.ainvoke(messages)
            logger.info("Closing message generated")
            return response.content
        except Exception as e:
            logger.error(f"Closing message generation error: {e}")
            return f"Great! Here's your payment link: {payment_link}\n\nFeel free to reach out if you have any questions!"

    async def generate_follow_up_message(self, user_data: Dict[str, Any], follow_up_count: int) -> str:
        """
        Generate a follow-up message based on follow-up count.

        Args:
            user_data: User data
            follow_up_count: Number of follow-ups sent so far

        Returns:
            Follow-up message
        """
        llm = self.get_llm_for_task("response")

        name = user_data.get("name", "there")
        stage = user_data.get("stage", "unknown")

        if follow_up_count == 0:
            context = "First follow-up after 2 hours. Be friendly and check if they have questions."
        elif follow_up_count == 1:
            context = "Second follow-up after 24 hours. Be understanding but remind them of the value."
        else:
            context = "Final automated follow-up. Be respectful and leave door open."

        prompt = f"""Generate a follow-up message for a customer.

Customer name: {name}
Stage: {stage}
Follow-up number: {follow_up_count + 1}
Context: {context}

The message should:
1. Be warm and non-pushy
2. Check in naturally
3. Offer help
4. Be brief (1-2 sentences)

Generate ONLY the message text."""

        try:
            messages = [HumanMessage(content=prompt)]
            response = await llm.ainvoke(messages)
            logger.info(f"Follow-up message generated (count: {follow_up_count})")
            return response.content
        except Exception as e:
            logger.error(f"Follow-up message generation error: {e}")
            return f"Hi {name}! Just checking in to see if you had any questions. I'm here to help!"

    async def generate_conversation_notes(self, user_data: Dict[str, Any], conversation_history: List[BaseMessage]) -> str:
        """
        Generate intelligent conversation notes using GPT-4o-mini.

        Args:
            user_data: Collected user data (name, email, phone, needs, etc.)
            conversation_history: Full conversation history

        Returns:
            Concise summary of the conversation with key insights
        """
        llm = self.get_llm_for_task("analysis")

        # Build conversation text
        conversation_text = []
        for msg in conversation_history:
            if isinstance(msg, HumanMessage):
                conversation_text.append(f"Cliente: {msg.content}")
            elif isinstance(msg, (BaseMessage,)):
                from langchain_core.messages import AIMessage
                if isinstance(msg, AIMessage):
                    conversation_text.append(f"Bot: {msg.content}")

        full_conversation = "\n".join(conversation_text[-10:])  # Last 10 messages max

        # Extract user data
        name = user_data.get("name", "Sin nombre")
        email = user_data.get("email", "")
        phone = user_data.get("phone", "")
        needs = user_data.get("needs", "")
        intent = user_data.get("intent", "")
        sentiment = user_data.get("sentiment", "")
        stage = user_data.get("stage", "")
        requests_human = user_data.get("requests_human", False)

        prompt = f"""Genera un resumen conciso y profesional de esta conversación de ventas.

DATOS DEL CLIENTE:
- Nombre: {name}
- Email: {email if email else "No proporcionado"}
- Teléfono: {phone if phone else "No proporcionado"}
- Necesidades: {needs if needs else "No especificadas"}
- Intención: {intent}
- Sentimiento: {sentiment}
- Etapa: {stage}
- Solicita humano: {"Sí" if requests_human else "No"}

ÚLTIMOS MENSAJES:
{full_conversation}

Genera UN SOLO PÁRRAFO (máximo 3-4 oraciones) que resuma:
1. Quién es el cliente y qué busca
2. Nivel de interés/compromiso
3. Próximos pasos recomendados

Formato: Texto plano, sin bullets, sin emojis, estilo profesional."""

        try:
            messages = [HumanMessage(content=prompt)]
            response = await llm.ainvoke(messages)
            logger.info("Conversation notes generated with LLM")
            return response.content.strip()
        except Exception as e:
            logger.error(f"Notes generation error: {e}")
            # Fallback to basic format
            return f"Cliente: {name} | Email: {email} | Tel: {phone} | Interés: {needs} | Etapa: {stage} | Intención: {intent} | Sentimiento: {sentiment}"


# Global instance (will be initialized in app.py)
llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get the global LLM service instance."""
    global llm_service
    if llm_service is None:
        llm_service = LLMService()
    return llm_service
