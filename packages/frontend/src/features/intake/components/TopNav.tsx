export default function TopNav() {
  return (
    <header className="top-nav">
      <div className="brand-mark" aria-label="iDEA star logo" />
      <nav aria-label="Main">
        <a className="active" href="#products">Products</a>
        <a href="#solutions">Solutions</a>
        <a href="#community">Community</a>
        <a href="#resources">Resources</a>
        <a href="#pricing">Pricing</a>
        <a href="#contact">Contact</a>
      </nav>
      <div className="nav-actions">
        <button className="ghost-button">Sign in</button>
        <button className="dark-button">Register</button>
      </div>
    </header>
  )
}
