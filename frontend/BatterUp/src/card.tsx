const Card: React.FC = () => {
    return (
    <div className="bg-black p-8 rounded-lg shadow-lg text-center">
        <div className="border-white border-2 bg-black p-8 rounded-lg">
            <div className="border-b-2 border-white p-2">
                <img src="src/assets/dude.jpg" className="w-48 h-48 rounded-full border-white border-2 mr-10 ml-16 mb-6"></img>
            </div>
            <div className="flex flex-col p-6 gap-1">
                <h1 className="text-3xl text-white">Player Name</h1>
                <h2 className="text-2xl text-white">Team Name</h2>
                <h2 className="text-xl text-white">Position Name</h2>
            </div>

            <div className="text-left">
                <h1 className="text-2xl text-white mb-3">Batting</h1>
                <div className="flex flex-row items-center space-x-4">
                    <h1 className="text-white text-xl">Contact</h1>
                    <svg width="200" height="2" className="text-white" xmlns="http://www.w3.org/2000/svg">
                        <line x1="0" y1="1" x2="200" y2="1" stroke="#E5E7EB" strokeWidth="2" />
                    </svg>
                    <h1 className="text-white text-xl">85</h1>
                </div>
                <div className="flex flex-row items-center space-x-4">
                    <h1 className="text-white text-xl mr-4">Power</h1>
                    <svg width="200" height="2" className="text-white" xmlns="http://www.w3.org/2000/svg">
                        <line x1="0" y1="1" x2="200" y2="1" stroke="#E5E7EB" strokeWidth="2" />
                    </svg>
                    <h1 className="text-white text-xl">90</h1>
                </div>
                <div className="flex flex-row items-center space-x-4">
                    <h1 className="text-white text-xl mr-4">Speed</h1>
                    <svg width="200" height="2" className="text-white" xmlns="http://www.w3.org/2000/svg">
                        <line x1="0" y1="1" x2="200" y2="1" stroke="#E5E7EB" strokeWidth="2" />
                    </svg>
                    <h1 className="text-white text-xl">89</h1>
                </div>

                <h1 className="text-2xl text-white mt-8 mb-3">Fielding</h1>
                <div className="flex flex-row items-center space-x-4">
                    <h1 className="text-white text-xl mr-4">Range</h1>
                    <svg width="200" height="2" className="text-white" xmlns="http://www.w3.org/2000/svg">
                        <line x1="0" y1="1" x2="200" y2="1" stroke="#E5E7EB" strokeWidth="2" />
                    </svg>
                    <h1 className="text-white text-xl">78</h1>
                </div>
                <div className="flex flex-row items-center space-x-3">
                    <h1 className="text-white text-xl">Accuracy</h1>
                    <svg width="200" height="2" className="text-white" xmlns="http://www.w3.org/2000/svg">
                        <line x1="0" y1="1" x2="200" y2="1" stroke="#E5E7EB" strokeWidth="2" />
                    </svg>
                    <h1 className="text-white text-xl ml-1">93</h1>
                </div>
            </div>

        </div>
    </div>
    );
  };
  
  export default Card;