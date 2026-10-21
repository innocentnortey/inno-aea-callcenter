export interface SseFrame {
  id: number | null;
  event: string;
  data: string;
  comment?: string;
}
/** Incremental text/event-stream parser: handles LF and CRLF, multi-line data, comments, split chunks. */
export class SseParser {
  private buffer = "";
  push(chunk: string): SseFrame[] {
    this.buffer += chunk;
    const frames: SseFrame[] = [];
    const norm = this.buffer.replace(/\r\n/g, "\n").replace(/\r(?!$)/g, "\n");
    const parts = norm.split("\n\n");
    this.buffer = parts.pop() ?? "";
    for (const block of parts) {
      if (!block.trim()) continue;
      let id: number | null = null;
      let event = "message";
      const data: string[] = [];
      let comment: string | undefined;
      for (const line of block.split("\n")) {
        if (line.startsWith(":")) comment = (comment ? comment + "\n" : "") + line.slice(1).trim();
        else if (line.startsWith("id:")) {
          const n = parseInt(line.slice(3).trim(), 10);
          id = Number.isNaN(n) ? null : n;
        } else if (line.startsWith("event:")) event = line.slice(6).trim() || "message";
        else if (line.startsWith("data:")) data.push(line.slice(5).replace(/^ /, ""));
      }
      const frame: SseFrame = { id, event, data: data.join("\n") };
      if (comment !== undefined) frame.comment = comment;
      frames.push(frame);
    }
    return frames;
  }
}
