from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib import colors
import uuid
import os
from datetime import datetime

def create_pdf(questions):
    # Ensure static directory exists
    static_dir = "static"
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    
    filename = f"{uuid.uuid4()}.pdf"
    filepath = os.path.join(static_dir, filename)
    
    # Create document with A4 size
    doc = SimpleDocTemplate(filepath, pagesize=A4, 
                          rightMargin=72, leftMargin=72, 
                          topMargin=72, bottomMargin=72)
    
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=24,
        spaceAfter=30,
        alignment=1,  # Center alignment
        textColor=colors.darkblue
    )
    
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading1'],
        fontSize=14,
        spaceAfter=20,
        textColor=colors.darkblue
    )
    
    question_style = ParagraphStyle(
        'QuestionStyle',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=12,
        leftIndent=20,
        firstLineIndent=-20
    )
    
    # Build the story
    story = []
    
    # Title
    story.append(Paragraph("Generated Question Paper", title_style))
    story.append(Spacer(1, 20))
    
    # Header information
    story.append(Paragraph(f"Date: {datetime.now().strftime('%B %d, %Y')}", header_style))
    story.append(Paragraph(f"Total Questions: {len(questions)}", header_style))
    story.append(Spacer(1, 20))
    
    # Instructions
    story.append(Paragraph("Instructions:", header_style))
    story.append(Paragraph("• Read each question carefully", styles['Normal']))
    story.append(Paragraph("• Answer all questions to the best of your ability", styles['Normal']))
    story.append(Paragraph("• Show your work where applicable", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Questions
    story.append(Paragraph("Questions:", header_style))
    
    for i, question in enumerate(questions, 1):
        question_text = f"{i}. {question}"
        story.append(Paragraph(question_text, question_style))
        story.append(Spacer(1, 8))
    
    # Footer
    story.append(PageBreak())
    story.append(Paragraph("End of Question Paper", styles['Normal']))
    
    # Build the PDF
    doc.build(story)
    return filepath
