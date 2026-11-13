import { render, screen } from '@testing-library/react'
import Home from './page'

describe('Home Page', () => {
  it('renders without crashing', () => {
    render(<Home />)
    expect(screen.getByText('Company Brain MVP')).toBeInTheDocument()
  })

  it('shows dashboard link', () => {
    render(<Home />)
    expect(screen.getByText('Go to Dashboard')).toBeInTheDocument()
  })

  it('shows API docs link', () => {
    render(<Home />)
    expect(screen.getByText('API Docs')).toBeInTheDocument()
  })
})