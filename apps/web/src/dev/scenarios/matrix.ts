// The 96-cell state matrix. The data lives in src/screens/matrix.ts (stubs list their real states from it);
// the dev layer re-exports it so scenario tests and the panel read it from here.
export { MATRIX, STANDARD_STATES, realStates } from "@/screens/matrix";
export type { MatrixCell } from "@/screens/matrix";
