import { Suspense } from 'react'
import { notFound } from 'next/navigation'
import { Container, VStack } from '@chakra-ui/react'
import SessionMetadata from './SessionMetadata'
import ClientActions from './ClientActions'
import { getSession } from '@/lib/sessions/getSession'

interface SessionPageProps {
  params: {
    id: string
  }
}

export default async function SessionPage({ params }: SessionPageProps) {
  const { id } = params
  
  // Fetch session data server-side with cache tags
  const sessionData = await getSession(id)
  
  if (!sessionData) {
    notFound()
  }

  return (
    <Container maxW="4xl" py={8}>
      <VStack spacing={6} align="stretch">
        {/* Session Metadata - Server Component */}
        <Suspense fallback={<div>Loading session details...</div>}>
          <SessionMetadata sessionData={sessionData} />
        </Suspense>

        {/* Interactive Actions - Client Component */}
        <Suspense fallback={<div>Loading actions...</div>}>
          <ClientActions 
            sessionId={sessionData.id}
            sessionData={sessionData}
          />
        </Suspense>
      </VStack>
    </Container>
  )
}

// Disable static generation for this dynamic route
export const dynamic = 'force-dynamic'