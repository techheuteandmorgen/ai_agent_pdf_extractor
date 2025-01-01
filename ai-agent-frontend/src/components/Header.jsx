const Header = ({ title }) => {
    return (
      <header className="bg-blue-600 text-white p-4 shadow-md">
        <h1 className="text-xl font-bold text-center">{title}</h1>
      </header>
    );
  };
  
  export default Header;