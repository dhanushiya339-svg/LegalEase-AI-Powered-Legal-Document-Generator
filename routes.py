import os

import requests
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


router = APIRouter()

load_dotenv()


class GenerateRequest(BaseModel):
	document_type: str
	parties: str
	terms: str
	effective_date: str
	language: str = "English"
	demo_mode: bool = True


@router.get("/health")
def health():
	return {"status": "ok"}


@router.post("/generate")
def generate_document(request: GenerateRequest):
	if not request.parties.strip() or not request.terms.strip():
		raise HTTPException(
			status_code=422,
			detail="Parties and terms are required.",
		)

	if request.demo_mode:
		terms = [term.strip() for term in request.terms.split(";") if term.strip()]
		document = "\n".join(
			[
				request.document_type,
				f"Effective date: {request.effective_date}",
			f"Language: {request.language}",
			"",
			f"Parties: {request.parties}",
			"",
			"Terms and conditions:",
			*[f"- {term}" for term in terms],
			"",
			"This demo draft is for review and is not legal advice.",
			]
		)
		return {
			"document": document,
			"model": "Demo Generator",
			"demo_mode": True,
		}

	api_key = os.getenv("GEMINI_API_KEY", "").strip()
	if not api_key:
		raise HTTPException(
			status_code=503,
			detail="Set GEMINI_API_KEY or enable Demo Mode.",
		)

	model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
	prompt = (
		f"Draft a {request.document_type} in {request.language}. "
		f"Effective date: {request.effective_date}. "
		f"Parties: {request.parties}. "
		f"Terms: {request.terms}. "
		"Return only the draft document. Include a brief note that it needs legal review."
	)

	try:
		response = requests.post(
			f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
			headers={"x-goog-api-key": api_key},
			json={"contents": [{"parts": [{"text": prompt}]}]},
			timeout=120,
		)
		response.raise_for_status()
		data = response.json()
		document = data["candidates"][0]["content"]["parts"][0]["text"]
	except requests.RequestException as exc:
		raise HTTPException(
			status_code=502,
			detail="The document generation service could not be reached.",
		) from exc
	except (KeyError, IndexError, TypeError):
		raise HTTPException(
			status_code=502,
			detail="The document generation service returned an invalid response.",
		)

	return {"document": document, "model": model, "demo_mode": False}
