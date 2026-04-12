import { render, screen } from "@testing-library/react";
import FormulaPanel from "../FormulaPanel";

describe("FormulaPanel", () => {
  it("renders deterministic formula text", () => {
    render(<FormulaPanel />);
    expect(screen.getByText(/deterministic scoring formula/i)).toBeInTheDocument();
    expect(screen.getByText(/0.5 \* normalized_apy/i)).toBeInTheDocument();
  });
});
