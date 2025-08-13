# 🧠 Intelligent Document Search System (RAG) Implementation Guide

## ⏱️ **Implementation Timeline: 4-7 hours**

---

## 📋 **Feature Overview**

### **What We're Building**
An intelligent document search system that allows users to upload their project files (PDFs, Word docs, text files) and then ask questions about them in natural conversation. This is a **Retrieval-Augmented Generation (RAG)** system that combines:

- **File Upload Pipeline**: Secure processing of user documents
- **Vector Search Database**: Semantic search through document content
- **Conversation Integration**: Seamless integration with existing Claude chat
- **Intelligent Context Injection**: Documents appear in conversation only when relevant

### **Why We're Building This**
**User Problem**: Creative professionals (Sarah/Emma) working on personal projects need to reference their own documents, notes, and research during conversations with the AI assistant. Currently, they have to manually copy-paste content or re-explain information they've already documented.

**Solution**: Enable users to upload their project files once, then ask questions like:
- "What did I write about the marketing strategy?"
- "What was I talking about the other day regarding timelines?"
- "Find the section about user personas in my document"
- "What deadlines did I mention in my notes?"

**Business Value**: 
- Increases user engagement and retention
- Makes the assistant more valuable for project work
- Reduces friction in accessing personal information
- Positions Fridays at Four as a comprehensive project companion

### **How It Works**

#### **1. Upload & Processing Flow**
```
User uploads PDF/DOCX/TXT → Text extraction → Chunking → OpenAI embeddings → Vector storage
```

#### **2. Search & Retrieval Flow**
```
User asks question → Keyword detection → Vector search → Document context → Claude response
```

#### **3. Conversation Integration**
- **Smart Detection**: Liberal keyword matching catches natural language queries
- **Context Injection**: Relevant document excerpts are injected into the conversation
- **Seamless Experience**: Users don't need to specify "search my documents" - it happens automatically
- **Preserved Caching**: Existing memory and prompt caching systems remain intact

#### **4. Technical Architecture**
- **OpenAI Embeddings**: Cost-effective at $0.02 per 1M tokens
- **PostgreSQL + pgvector**: Vector database with HNSW indexing for fast search
- **Claude API**: Processes document context and generates responses
- **FastAPI Backend**: Handles upload, processing, and search endpoints

---

## 🎯 **What We Have vs. What We Need**

### **✅ What We Have (70% Complete)**

#### **Branch: `feat/file-upload-vector-search`**
- **Upload Pipeline**: Complete processing system ready to integrate
- **Database Schema**: Production-ready tables with security features
- **API Endpoints**: `/upload-files/{user_id}` and `/search-documents/{user_id}`

**Specific Files to Copy:**
- `src/text_extractor.py` - PDF/DOCX/TXT extraction
- `src/file_validation.py` - Security validation  
- `src/text_chunker.py` - Text chunking for embeddings
- `src/embedding_service.py` - OpenAI embedding generation
- `src/database_storage.py` - Database storage operations
- `src/pipeline_orchestrator.py` - Coordinates entire upload process
- `supabase/migrations/20250623_add_file_upload_vector_search.sql` - Database tables

#### **Branch: `RAG-working-need-conversation-retrieval`**
- **Search Logic**: Working LangChain-based retrieval system
- **Vector Functions**: `match_documents` RPC for similarity search (⚠️ **VERIFY THIS EXISTS**)
- **Integration Pattern**: Conversation-aware document search
- **working RAG syste**: this is a fully working RAG framework
that I built 9 months ago that we're using as the foundation for this feature

**Specific Files to Reference:**
- `rag_model.py` - LangChain implementation (for reference only)
- `transcript_search.py` - Search integration pattern

#### **Current Architecture (`working-branch`)**
- **FastAPI Backend**: `src/main.py` with Claude agent integration
- **Database**: Supabase PostgreSQL with pgvector extension
- **AI Integration**: `src/claude_agent.py` handles all conversations

---

## 🔧 **What We Need to Build**

### **Integration Tasks**
1. **Port upload pipeline** from feature branch to main
2. **Rewrite LangChain RAG** to use direct Claude API calls
3. **Add document search** to existing conversation flow
4. **Implement liberal keyword detection** for search triggering
5. **Add vector indexing** for performance

### **Missing Components**
- `src/document_search.py` - Direct Claude API search (replacing LangChain)
- Database migration for HNSW vector indexing
- Integration with `claude_agent.py` for search detection
- Error handling and logging for document operations

---

## 🗄️ **Database Schema Setup**

### **Step 1: Create Migration**
```bash
# Create new migration file
cd supabase/migrations
touch $(date +%Y%m%d)_add_file_upload_search.sql
```

### **Step 2: Add Tables and Indexes**
```sql
-- Copy from feat/file-upload-vector-search branch
-- File: supabase/migrations/20250623_add_file_upload_vector_search.sql

-- Key tables: user_files, file_chunks, file_processing_logs
-- (Copy the existing table definitions from the migration file)

-- CRITICAL: Add HNSW index for performance (ADD THIS TO THE MIGRATION)
CREATE INDEX file_chunks_embedding_hnsw
ON file_chunks USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Create or verify the match_documents RPC function
CREATE OR REPLACE FUNCTION match_documents(
    p_user_id text,
    p_query_embedding vector(1536),
    p_top_k int DEFAULT 5,
    p_threshold float DEFAULT 0.7
)
RETURNS TABLE(
    content text,
    similarity float,
    file_name text,
    chunk_index int
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        fc.content,
        1 - (fc.embedding <=> p_query_embedding) as similarity,
        uf.file_name,
        fc.chunk_index
    FROM file_chunks fc
    JOIN user_files uf ON fc.file_id = uf.id
    WHERE uf.user_id = p_user_id
    AND 1 - (fc.embedding <=> p_query_embedding) > p_threshold
    ORDER BY fc.embedding <=> p_query_embedding
    LIMIT p_top_k;
END;
$$;
```

### **Step 3: Verify RPC Function Exists**
```sql
-- Check if match_documents function exists
SELECT routine_name FROM information_schema.routines 
WHERE routine_name = 'match_documents';

-- If it doesn't exist, the function is included in Step 2 migration above
-- If it exists, verify it has the correct signature:
SELECT routine_name, routine_type, data_type 
FROM information_schema.routines 
WHERE routine_name = 'match_documents';
```

### **Step 4: Run Migration**
```bash
# Apply the migration
supabase db push

# Verify tables exist
supabase db show
# Should show: user_files, file_chunks, file_processing_logs

# Test the RPC function
psql -h localhost -p 54322 -U postgres -d postgres -c "
SELECT match_documents(
    'test-user',
    '[0.1,0.2,0.3]'::vector(1536),
    5,
    0.7
);
"
```

---

## 📁 **File Integration Steps**

### **Phase 1: Create Feature Branch & Copy Upload Pipeline**
```bash
# Create new feature branch from working-branch
git checkout working-branch
git pull origin working-branch
git checkout -b feat/file-upload-integration

# Copy files from upload branch
git checkout feat/file-upload-vector-search

# Copy processing files to new branch
git checkout feat/file-upload-integration
git checkout feat/file-upload-vector-search -- src/text_extractor.py
git checkout feat/file-upload-vector-search -- src/file_validation.py
git checkout feat/file-upload-vector-search -- src/text_chunker.py
git checkout feat/file-upload-vector-search -- src/embedding_service.py
git checkout feat/file-upload-vector-search -- src/database_storage.py
git checkout feat/file-upload-vector-search -- src/pipeline_orchestrator.py
git checkout feat/file-upload-vector-search -- supabase/migrations/20250623_add_file_upload_vector_search.sql

# Verify files copied
ls -la src/ | grep -E "(text_extractor|file_validation|text_chunker|embedding_service|database_storage|pipeline_orchestrator)"
```

### **Phase 2: Create Document Search Module**
Create `src/document_search.py`:
```python
import asyncio
from typing import List, Dict, Any, Optional
from embedding_service import EmbeddingService
from config import get_supabase_client
from claude_client_simple import ClaudeClient
import re

class DocumentSearch:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.supabase = get_supabase_client()
        self.claude_client = ClaudeClient()
    
    async def search_and_respond(self, query: str, user_id: str, thread_id: str) -> str:
        """Replace LangChain ConversationalRetrievalChain with direct Claude API"""
        
        # 1. Generate embedding for query
        query_embedding = await self.embedding_service.embed_text(query)
        
        # 2. Search documents (uses HNSW index if available, falls back to seq scan)
        search_results = await self.supabase.rpc("match_documents", {
            "p_user_id": user_id,
            "p_query_embedding": query_embedding,
            "p_top_k": 5,
            "p_threshold": 0.7
        })
        
        if not search_results.data:
            return None  # No relevant documents found
        
        # 3. Format context for injection into existing conversation
        context = self._format_document_context(search_results.data)
        
        # 4. Return context to inject into existing Claude conversation
        # (Don't call Claude directly - let existing system handle conversation + caching)
        return context

    def _format_document_context(self, search_results: List[Dict]) -> str:
        """Format document chunks for injection into existing conversation"""
        context_parts = ["Based on your uploaded documents:"]
        for i, result in enumerate(search_results, 1):
            context_parts.append(f"{i}. {result['content']}")
        return "\n".join(context_parts)
```

### **Phase 3: Integrate with Claude Agent**
Modify `src/claude_agent.py`:
```python
# Add to imports
from document_search import DocumentSearch

# Add to ReactAgent.__init__
self.document_search = DocumentSearch()

# Add search detection method
def _should_search_documents(self, user_message: str) -> bool:
    """Detect if user might be asking about their documents - liberal detection"""
    # Liberal patterns that catch various ways people ask about content
    patterns = [
        r'\b(my|the) (file|document|doc|notes|pdf|upload)\b',
        r'\bwhat (did|do) I (write|say|mention|talk about|upload)\b',
        r'\b(remember|recall) (what|when) I (wrote|said|mentioned|uploaded)\b',
        r'\bin (my|the) (file|document|doc|notes|pdf|upload)\b',
        r'\baccording to (my|the) (file|document|doc|notes|pdf|upload)\b',
        r'\bfind.*in.*(file|document|doc|notes|pdf|upload)\b',
        r'\bwhat was I (talking|writing) about\b',
        r'\bthe other day I (wrote|mentioned|said|uploaded)\b',
        r'\b(check|look at) (my|the) (file|document|doc|notes|pdf|upload)\b',
        r'\bI (wrote|mentioned|said|uploaded) (something|this)\b',
        r'\b(earlier|before) I (wrote|said|mentioned|uploaded)\b'
    ]
    
    user_message_lower = user_message.lower()
    return any(re.search(pattern, user_message_lower) for pattern in patterns)

# Alternative: Always search documents and let semantic similarity decide
# This is simpler but may add latency - depends on performance requirements
def _should_search_documents_always(self, user_message: str) -> bool:
    """Always search documents and let vector similarity decide relevance"""
    return True  # Let semantic search determine if documents are relevant

# Modify send_message method
async def send_message(self, messages: List[Dict[str, str]]) -> str:
    user_message = messages[-1]["content"]
    
    # Check if we should search documents
    if self._should_search_documents(user_message):
        document_context = await self.document_search.search_and_respond(
            user_message, 
            self.user_id, 
            self.thread_id
        )
        
        if document_context:
            # Inject document context into the system message
            # This preserves existing memory/prompt caching system
            system_message = f"{document_context}\n\nNow respond to the user's question."
            messages.insert(0, {"role": "system", "content": system_message})
    
    # Continue with normal Claude conversation (with injected context if found)
    # ... existing logic (memory retrieval, prompt caching, etc.)
```

### **Phase 4: Add Upload Endpoint**
Add to `src/main.py`:
```python
from pipeline_orchestrator import PipelineOrchestrator

# Add global instance
pipeline_orchestrator = PipelineOrchestrator()

@app.post("/upload-files/{user_id}")
async def upload_files(user_id: str, files: List[UploadFile]):
    """Upload and process files for user"""
    try:
        await memory.ensure_creator_profile(user_id)
        
        results = []
        for file in files:
            result = await pipeline_orchestrator.process_file(file, user_id)
            results.append(result)
        
        return {"status": "success", "results": results}
    
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/documents/{user_id}")
async def get_user_documents(user_id: str):
    """Get list of user's uploaded documents - for frontend to show document list"""
    try:
        supabase = get_supabase_client()
        result = await supabase.table("user_files").select("*").eq("user_id", user_id).execute()
        return {"documents": result.data}
    except Exception as e:
        logger.error(f"Document list failed: {e}")
        return {"status": "error", "message": str(e)}
        
# Note: This endpoint is for frontend UI to show "My Documents" list
# NOT for search functionality - that's handled in the conversation flow
```

---

## 🧪 **Testing & Validation**

### **Phase 1: Test Upload Pipeline**
```bash
# 1. Test file upload endpoint
curl -X POST "http://localhost:8000/upload-files/test-user" \
  -F "files=@test-document.pdf" \
  -F "files=@another-doc.txt"

# Expected response:
# {"status": "success", "results": [{"file_id": "...", "chunks_created": 15}]}
```

### **Phase 2: Verify Database Storage**
```sql
-- Check file was stored
SELECT * FROM user_files WHERE user_id = 'test-user';

-- Check chunks were created
SELECT COUNT(*) FROM file_chunks fc
JOIN user_files uf ON fc.file_id = uf.id
WHERE uf.user_id = 'test-user';

-- Test vector search directly
SELECT content, 1 - (embedding <=> '[0.1,0.2,0.3]'::vector(1536)) as similarity
FROM file_chunks fc
JOIN user_files uf ON fc.file_id = uf.id
WHERE uf.user_id = 'test-user'
ORDER BY embedding <=> '[0.1,0.2,0.3]'::vector(1536)
LIMIT 5;
```

### **Phase 3: Test Document Search Integration**
```bash
# 1. Test normal conversation (should work as before)
curl -X POST "http://localhost:8000/chat/test-user" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, how are you?"}'

# 2. Test document search trigger
curl -X POST "http://localhost:8000/chat/test-user" \
  -H "Content-Type: application/json" \
  -d '{"message": "What does my document say about project planning?"}'

# 3. Test liberal keyword detection
curl -X POST "http://localhost:8000/chat/test-user" \
  -H "Content-Type: application/json" \
  -d '{"message": "What was I writing about the other day?"}'

# 4. Test semantic search
curl -X POST "http://localhost:8000/chat/test-user" \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me about deadlines and timelines"}'
```

### **Phase 4: Test Document List Endpoint**
```bash
# Test document list for frontend
curl -X GET "http://localhost:8000/documents/test-user"

# Expected response:
# {"documents": [{"id": "...", "file_name": "test-document.pdf", "upload_date": "..."}]}
```

---

## 🎨 **Frontend Integration**

### **File Upload Button**
Add to your frontend (React example):
```jsx
// FileUpload.tsx
import React, { useState } from 'react';

const FileUpload = ({ userId }) => {
  const [uploading, setUploading] = useState(false);
  const [files, setFiles] = useState([]);

  const handleFileUpload = async (event) => {
    const selectedFiles = Array.from(event.target.files);
    setUploading(true);
    
    const formData = new FormData();
    selectedFiles.forEach(file => {
      formData.append('files', file);
    });

    try {
      const response = await fetch(`/api/upload-files/${userId}`, {
        method: 'POST',
        body: formData,
      });
      
      const result = await response.json();
      if (result.status === 'success') {
        alert('Files uploaded successfully!');
        // Refresh document list
        fetchDocuments();
      }
    } catch (error) {
      alert('Upload failed: ' + error.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <input
        type="file"
        multiple
        accept=".pdf,.docx,.txt"
        onChange={handleFileUpload}
        disabled={uploading}
      />
      {uploading && <p>Uploading...</p>}
    </div>
  );
};
```

### **Document List Display**
```jsx
// DocumentList.tsx
const DocumentList = ({ userId }) => {
  const [documents, setDocuments] = useState([]);

  useEffect(() => {
    fetchDocuments();
  }, [userId]);

  const fetchDocuments = async () => {
    const response = await fetch(`/api/documents/${userId}`);
    const data = await response.json();
    setDocuments(data.documents || []);
  };

  return (
    <div>
      <h3>My Documents</h3>
      {documents.map(doc => (
        <div key={doc.id}>
          <span>{doc.file_name}</span>
          <span>{new Date(doc.upload_date).toLocaleDateString()}</span>
        </div>
      ))}
    </div>
  );
};
```

---

## 🔧 **Troubleshooting**

### **Common Issues**

**1. Import Errors**
```bash
# If you get "ModuleNotFoundError"
# Make sure all files are in src/ directory
# Check Python path in your environment
```

**2. Database Connection**
```bash
# If RPC function fails
# Check Supabase connection
supabase status
# Should show all services running
```

**3. Vector Search Returns No Results**
```sql
-- Check if embeddings were created
SELECT COUNT(*) FROM file_chunks WHERE embedding IS NOT NULL;

-- Check embedding dimensions
SELECT array_length(embedding, 1) FROM file_chunks LIMIT 1;
-- Should return 1536
```

**4. File Upload Fails**
```bash
# Check file size limits
# Check file type validation
# Check disk space
```

**5. HNSW Index Not Being Used**
```sql
-- Check if index exists
SELECT indexname FROM pg_indexes WHERE tablename = 'file_chunks';

-- Force index rebuild if needed
REINDEX INDEX file_chunks_embedding_hnsw;
```

---

## 🚀 **Deployment Considerations**

### **Environment Variables**
```bash
# Add to .env
OPENAI_API_KEY=your_openai_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

### **Production Checklist**
- [ ] File upload size limits configured
- [ ] File type validation enabled
- [ ] HNSW index created and optimized
- [ ] Error logging implemented
- [ ] Rate limiting on upload endpoint
- [ ] Disk space monitoring
- [ ] Embedding service error handling

---

## ⚠️ **Important Notes**

### **Performance**
- **HNSW index is critical** - Added in Step 2 database migration above
- **Without HNSW**: Vector search uses sequential scan (slow for large datasets)
- **With HNSW**: Sub-second search even with millions of vectors
- **OpenAI embeddings are cheap** ($0.02 per 1M tokens)
- **Claude API calls only happen when documents are found**
- **Vector search happens before Claude call** - saves API costs when no docs match

### **Error Handling**
- All file operations should have try-catch blocks
- Log errors to help with debugging
- Graceful degradation when documents aren't found

### **Security**
- File validation prevents malicious uploads
- User isolation in database queries
- Size limits prevent resource exhaustion

---

## 🎯 **Success Criteria & Testing Checklist**

### **Phase 1: Upload Pipeline ✅**
- [ ] User can upload PDF, DOCX, TXT files via `/upload-files/{user_id}`
- [ ] Files are validated for security and size
- [ ] Files are processed (extracted, chunked, embedded)
- [ ] Data is stored in `user_files` and `file_chunks` tables
- [ ] Upload endpoint returns success/error status

### **Phase 2: Database & Search ✅**
- [ ] HNSW index is created and functional
- [ ] `match_documents` RPC function works correctly
- [ ] Vector search returns relevant results
- [ ] Search performance is sub-second for typical queries
- [ ] User isolation works (users only see their own documents)

### **Phase 3: Conversation Integration ✅**
- [ ] Liberal keyword detection triggers document search
- [ ] Document context is injected into conversation
- [ ] Normal conversations work unchanged
- [ ] Existing memory/prompt caching system is preserved
- [ ] Search results are formatted clearly for Claude

### **Phase 4: Frontend Integration ✅**
- [ ] File upload button works on frontend
- [ ] Document list displays user's files
- [ ] Upload progress is shown to user
- [ ] Error messages are user-friendly
- [ ] Multiple file upload supported

### **Phase 5: Production Readiness ✅**
- [ ] Error handling and logging implemented
- [ ] Rate limiting on upload endpoint
- [ ] File size and type validation
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] Performance monitoring in place

---

## 🎉 **Next Steps After Implementation**

### **Phase 2 Enhancements (Future)**
1. **Semantic Search Always-On**: Remove keyword detection, always search documents
2. **Document Metadata**: Add file type, upload date, size to search results
3. **Multi-Document Queries**: "Compare what I said in doc A vs doc B"
4. **Document Summarization**: "Summarize all my uploaded documents"
5. **Citation Links**: Show which specific document/page info came from

### **Advanced Features (Future)**
1. **File Type Expansion**: Add support for XLSX, PPTX, CSV
2. **OCR Integration**: Extract text from scanned PDFs and images
3. **Document Versioning**: Track document updates and changes
4. **Collaborative Documents**: Share documents between users
5. **Document Analytics**: Track which documents are searched most

---

## 📋 **Implementation Summary**

**What You're Building**: Intelligent document search system (RAG) that allows users to upload project files and ask questions about them in natural conversation

**Key Architecture Decisions**:
- ✅ OpenAI embeddings (cheap, compatible with Claude)
- ✅ HNSW indexing (fast vector search)
- ✅ Keyword-triggered search (Phase 1 approach)
- ✅ Context injection (preserves existing memory/caching)
- ✅ Feature branch workflow (safe development)

**Estimated Implementation Time: 4-7 hours**

**Risk Level: Low** - Most components already exist, primarily integration work 