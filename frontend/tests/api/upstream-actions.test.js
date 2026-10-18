import { beforeEach, describe, expect, it, vi } from 'vitest'

const request = vi.hoisted(() => ({ delete: vi.fn(), post: vi.fn() }))
vi.mock('@/utils/request', () => ({ default: request }))
import { deleteAgentSession } from '@/api/agent'
import { undoAction } from '@/api/undo'
import { reprocessTrainingDataset } from '@/api/training'

describe('upstream actions on release API contracts', () => {
  beforeEach(() => vi.clearAllMocks())

  it('deletes through the reversible chat endpoint and forwards its undo token', async () => {
    request.delete.mockResolvedValue({ undo_id: 'undo-token' })
    const result = await deleteAgentSession('chat/with space')
    await undoAction(result.undo_id)
    expect(request.delete).toHaveBeenCalledWith('/chat/sessions/chat%2Fwith%20space')
    expect(request.post).toHaveBeenCalledWith('/undo/undo-token')
  })

  it('surfaces revalidation failures to the per-item bulk feedback', async () => {
    const error = new Error('invalid dataset')
    request.post.mockRejectedValue(error)
    await expect(reprocessTrainingDataset('dataset with space')).rejects.toBe(error)
    expect(request.post).toHaveBeenCalledWith('/training/datasets/dataset%20with%20space/reprocess')
  })
})
