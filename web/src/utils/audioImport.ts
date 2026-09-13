import { api } from '@/api'

// Keep each pywebview call comfortably below WebView2's practical message size.
const AUDIO_CHUNK_SIZE = 256 * 1024

function readBlobDataUrl(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result || ''))
    reader.onerror = () => reject(new Error('无法读取拖入的音频文件'))
    reader.readAsDataURL(blob)
  })
}

/** Return a path the Python side can open, including large WebView drag-and-drop files. */
export async function importDroppedAudio(file: File): Promise<string | null> {
  const nativePath = String((file as File & { path?: string }).path || '').trim()
  if (nativePath) return nativePath

  const token = await api.startAudioImport(file.name)
  if (!token) return null

  let finished = false
  try {
    for (let offset = 0; offset < file.size; offset += AUDIO_CHUNK_SIZE) {
      const chunk = file.slice(offset, Math.min(file.size, offset + AUDIO_CHUNK_SIZE))
      const accepted = await api.appendAudioImport(token, await readBlobDataUrl(chunk))
      if (!accepted) throw new Error('无法写入拖入的音频文件')
    }
    const path = String(await api.finishAudioImport(token) || '').trim()
    finished = Boolean(path)
    return path || null
  } finally {
    if (!finished) await api.cancelAudioImport(token)
  }
}
